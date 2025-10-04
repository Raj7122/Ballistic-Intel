"""
Unit Tests for Orchestrator
Tests DAG execution, error handling, and context tracking
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date

from orchestrator.context import RunContext
from orchestrator.dag import DAG, DAGNode, NodeStatus
from orchestrator.errors import (
    OrchestratorError,
    AgentExecutionError,
    write_to_dlq,
    list_dlq_files,
    read_dlq_file
)
from config.orchestrator_config import OrchestratorConfig


class TestRunContext:
    """Test RunContext"""
    
    def test_context_creation(self):
        """Test creating a run context"""
        ctx = RunContext(
            run_mode="incremental",
            start_date="2024-01-01",
            end_date="2024-01-03"
        )
        
        assert ctx.run_mode == "incremental"
        assert ctx.start_date == "2024-01-01"
        assert ctx.end_date == "2024-01-03"
        assert len(ctx.correlation_id) > 0
        assert ctx.stats == {}
        assert ctx.errors == []
    
    def test_increment_stat(self):
        """Test incrementing statistics"""
        ctx = RunContext()
        
        ctx.increment('items_processed')
        assert ctx.get_stat('items_processed') == 1
        
        ctx.increment('items_processed', 5)
        assert ctx.get_stat('items_processed') == 6
    
    def test_add_error(self):
        """Test adding errors"""
        ctx = RunContext()
        
        ctx.add_error('p1a_patents', 'Connection timeout', 'US-123')
        
        assert len(ctx.errors) == 1
        assert ctx.errors[0]['node'] == 'p1a_patents'
        assert ctx.errors[0]['message'] == 'Connection timeout'
        assert ctx.errors[0]['item_id'] == 'US-123'
    
    def test_to_dict(self):
        """Test converting context to dict"""
        ctx = RunContext(run_mode="dry_run")
        ctx.increment('test', 10)
        
        result = ctx.to_dict()
        
        assert result['run_mode'] == 'dry_run'
        assert result['stats']['test'] == 10
        assert 'correlation_id' in result
        assert 'duration_seconds' in result


class TestDAG:
    """Test DAG execution"""
    
    def test_add_node(self):
        """Test adding nodes to DAG"""
        dag = DAG()
        
        def dummy_fn(ctx):
            return {'success': True}
        
        node = DAGNode(name='test_node', fn=dummy_fn)
        dag.add_node(node)
        
        assert 'test_node' in dag.nodes
        assert dag.nodes['test_node'].name == 'test_node'
    
    def test_validate_missing_dependency(self):
        """Test validation catches missing dependencies"""
        dag = DAG()
        
        dag.add_node(DAGNode(name='node_a', fn=lambda ctx: {}, dependencies=['node_b']))
        
        with pytest.raises(ValueError, match="non-existent"):
            dag.validate()
    
    def test_validate_cycle_detection(self):
        """Test validation catches cycles"""
        dag = DAG()
        
        dag.add_node(DAGNode(name='node_a', fn=lambda ctx: {}, dependencies=['node_b']))
        dag.add_node(DAGNode(name='node_b', fn=lambda ctx: {}, dependencies=['node_a']))
        
        with pytest.raises(ValueError, match="cycle"):
            dag.validate()
    
    def test_execution_order(self):
        """Test topological sort for execution order"""
        dag = DAG()
        
        dag.add_node(DAGNode(name='node_c', fn=lambda ctx: {}, dependencies=['node_a', 'node_b']))
        dag.add_node(DAGNode(name='node_b', fn=lambda ctx: {}, dependencies=['node_a']))
        dag.add_node(DAGNode(name='node_a', fn=lambda ctx: {}, dependencies=[]))
        
        order = dag.get_execution_order()
        
        # node_a must come before node_b and node_c
        assert order.index('node_a') < order.index('node_b')
        assert order.index('node_a') < order.index('node_c')
        # node_b must come before node_c
        assert order.index('node_b') < order.index('node_c')
    
    def test_execute_success(self):
        """Test successful DAG execution"""
        dag = DAG()
        ctx = RunContext()
        
        # Create mock nodes
        def node_a_fn(ctx):
            ctx.increment('a_ran')
            return {'result': 'a'}
        
        def node_b_fn(ctx):
            ctx.increment('b_ran')
            return {'result': 'b'}
        
        dag.add_node(DAGNode(name='node_a', fn=node_a_fn))
        dag.add_node(DAGNode(name='node_b', fn=node_b_fn, dependencies=['node_a']))
        
        summary = dag.execute(ctx)
        
        assert summary['completed'] == 2
        assert summary['failed'] == 0
        assert ctx.get_stat('a_ran') == 1
        assert ctx.get_stat('b_ran') == 1
    
    def test_execute_with_failure(self):
        """Test DAG execution with node failure"""
        dag = DAG()
        ctx = RunContext()
        
        def node_a_fn(ctx):
            raise Exception("Simulated failure")
        
        def node_b_fn(ctx):
            ctx.increment('b_ran')
            return {'result': 'b'}
        
        dag.add_node(DAGNode(name='node_a', fn=node_a_fn))
        dag.add_node(DAGNode(name='node_b', fn=node_b_fn, dependencies=['node_a']))
        
        summary = dag.execute(ctx, fail_fast=False)
        
        assert summary['failed'] == 1
        assert summary['skipped'] == 1
        assert ctx.get_stat('b_ran') == 0  # node_b skipped


class TestDLQ:
    """Test DLQ (dead letter queue) functionality"""
    
    def test_write_to_dlq(self, tmp_path):
        """Test writing to DLQ"""
        dlq_dir = str(tmp_path / "dlq")
        
        payload = {'item_id': 'test-123', 'data': 'sample'}
        filepath = write_to_dlq(
            dlq_dir=dlq_dir,
            node_name='p2_relevance',
            payload=payload,
            error_message='Classification timeout',
            item_id='test-123'
        )
        
        assert filepath.endswith('.json')
        assert 'p2_relevance' in filepath
        
        # Verify file exists
        import os
        assert os.path.exists(filepath)
    
    def test_list_dlq_files(self, tmp_path):
        """Test listing DLQ files"""
        import time
        dlq_dir = str(tmp_path / "dlq")
        
        # Write multiple DLQ files with slight delays to ensure unique timestamps
        write_to_dlq(dlq_dir, 'p2_relevance', {'id': '1'}, 'error1', 'item-1')
        time.sleep(0.01)  # Ensure different timestamp
        write_to_dlq(dlq_dir, 'p2_relevance', {'id': '2'}, 'error2', 'item-2')
        time.sleep(0.01)
        write_to_dlq(dlq_dir, 'p3_extraction', {'id': '3'}, 'error3', 'item-3')
        
        # List all files
        all_files = list_dlq_files(dlq_dir)
        assert len(all_files) == 3
        
        # List by node
        p2_files = list_dlq_files(dlq_dir, 'p2_relevance')
        assert len(p2_files) == 2
    
    def test_read_dlq_file(self, tmp_path):
        """Test reading a DLQ file"""
        dlq_dir = str(tmp_path / "dlq")
        
        payload = {'item_id': 'test-456', 'title': 'Test Patent'}
        filepath = write_to_dlq(dlq_dir, 'p1a_patents', payload, 'Parse error')
        
        # Read it back
        entry = read_dlq_file(filepath)
        
        assert entry['node'] == 'p1a_patents'
        assert entry['error'] == 'Parse error'
        assert entry['payload']['item_id'] == 'test-456'


class TestOrchestratorConfig:
    """Test Orchestrator Configuration"""
    
    def test_get_date_range_incremental(self):
        """Test date range calculation for incremental mode"""
        with patch.dict('os.environ', {'RUN_MODE': 'incremental', 'LOOKBACK_DAYS': '2'}):
            from config.orchestrator_config import OrchestratorConfig
            
            start, end = OrchestratorConfig.get_date_range()
            
            # Should be 2 days ago to today
            from datetime import datetime, timedelta
            expected_start = (datetime.utcnow().date() - timedelta(days=2)).isoformat()
            expected_end = datetime.utcnow().date().isoformat()
            
            assert start == expected_start
            assert end == expected_end
    
    def test_get_date_range_backfill(self):
        """Test date range for backfill mode"""
        import importlib
        with patch.dict('os.environ', {
            'RUN_MODE': 'backfill',
            'START_DATE': '2024-12-01',
            'END_DATE': '2024-12-07'
        }, clear=True):
            # Reload module to pick up new env vars
            import config.orchestrator_config
            importlib.reload(config.orchestrator_config)
            from config.orchestrator_config import OrchestratorConfig
            
            start, end = OrchestratorConfig.get_date_range()
            
            assert start == '2024-12-01'
            assert end == '2024-12-07'
    
    def test_is_dry_run(self):
        """Test dry run detection"""
        import importlib
        with patch.dict('os.environ', {'RUN_MODE': 'dry_run'}, clear=True):
            # Reload module to pick up new env vars
            import config.orchestrator_config
            importlib.reload(config.orchestrator_config)
            from config.orchestrator_config import OrchestratorConfig
            
            assert OrchestratorConfig.is_dry_run() is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

