"""
Orchestrator Runner
Coordinates all agents (P1a, P1b, P2, P3, P4) and storage layer
"""
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.orchestrator_config import OrchestratorConfig
from orchestrator.context import RunContext
from orchestrator.dag import DAG, DAGNode
from orchestrator.errors import PreflightCheckError, write_to_dlq

# Import agents
from agents.p1a_patent_ingestion import PatentIngestionAgent
from agents.p1b_newsletter_ingestion import NewsletterIngestionAgent
from agents.p2_relevance_filter import RelevanceFilterAgent
from agents.p3_extraction_classifier import ExtractionClassifierAgent
from agents.p4_entity_resolution import EntityResolutionAgent

# Import storage
from services.storage_writer import get_storage_writer

# Import models
from models.patent import Patent
from models.news_article import NewsArticle

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Main orchestrator for the Ballistic Intel pipeline
    """
    
    def __init__(self, config: OrchestratorConfig = OrchestratorConfig):
        self.config = config
        self.storage = get_storage_writer()
        
        # Initialize agents
        self.p1a_agent = PatentIngestionAgent()
        self.p1b_agent = NewsletterIngestionAgent()
        self.p2_agent = RelevanceFilterAgent()
        self.p3_agent = ExtractionClassifierAgent()
        self.p4_agent = EntityResolutionAgent()
        
        # Build DAG
        self.dag = self._build_dag()
    
    def _build_dag(self) -> DAG:
        """Build the pipeline DAG"""
        dag = DAG()
        
        # Node 1: Ingest patents (P1a)
        dag.add_node(DAGNode(
            name="p1a_patents",
            fn=self._run_p1a,
            dependencies=[]
        ))
        
        # Node 2: Ingest news (P1b)
        dag.add_node(DAGNode(
            name="p1b_news",
            fn=self._run_p1b,
            dependencies=[]
        ))
        
        # Node 3: Filter relevance (P2) - depends on P1a and P1b
        dag.add_node(DAGNode(
            name="p2_relevance",
            fn=self._run_p2,
            dependencies=["p1a_patents", "p1b_news"]
        ))
        
        # Node 4: Extract entities (P3) - depends on P2
        dag.add_node(DAGNode(
            name="p3_extraction",
            fn=self._run_p3,
            dependencies=["p2_relevance"]
        ))
        
        # Node 5: Resolve entities (P4) - depends on P3
        dag.add_node(DAGNode(
            name="p4_resolution",
            fn=self._run_p4,
            dependencies=["p3_extraction"]
        ))
        
        return dag
    
    def _run_p1a(self, ctx: RunContext) -> Dict[str, Any]:
        """Run Agent P1a: Patent Ingestion"""
        logger.info(f"[P1a] Ingesting patents from {ctx.start_date} to {ctx.end_date}")
        
        if ctx.is_dry_run:
            logger.info("[P1a] Dry run mode - skipping actual ingestion")
            return {'patents': [], 'count': 0}
        
        try:
            # Ingest patents
            patents = self.p1a_agent.ingest_patents(ctx.start_date, ctx.end_date)
            ctx.increment('p1a_patents_fetched', len(patents))
            
            logger.info(f"[P1a] Fetched {len(patents)} patents")
            
            # Persist
            result = self.storage.persist_patents(patents)
            ctx.increment('p1a_patents_persisted', result.get('count', 0))
            
            if not result.get('success'):
                raise Exception(f"Failed to persist patents: {result.get('error')}")
            
            return {'patents': patents, 'count': len(patents)}
        
        except Exception as e:
            logger.error(f"[P1a] Error: {e}", exc_info=True)
            ctx.add_error('p1a_patents', str(e))
            raise
    
    def _run_p1b(self, ctx: RunContext) -> Dict[str, Any]:
        """Run Agent P1b: Newsletter Ingestion"""
        logger.info(f"[P1b] Ingesting news from {ctx.start_date} to {ctx.end_date}")
        
        if ctx.is_dry_run:
            logger.info("[P1b] Dry run mode - skipping actual ingestion")
            return {'articles': [], 'count': 0}
        
        try:
            # Ingest news
            articles = self.p1b_agent.ingest_newsletters(lookback_days=self.config.LOOKBACK_DAYS)
            ctx.increment('p1b_articles_fetched', len(articles))
            
            logger.info(f"[P1b] Fetched {len(articles)} news articles")
            
            # Persist
            result = self.storage.persist_news(articles)
            ctx.increment('p1b_articles_persisted', result.get('count', 0))
            
            if not result.get('success'):
                raise Exception(f"Failed to persist news: {result.get('error')}")
            
            return {'articles': articles, 'count': len(articles)}
        
        except Exception as e:
            logger.error(f"[P1b] Error: {e}", exc_info=True)
            ctx.add_error('p1b_news', str(e))
            raise
    
    def _run_p2(self, ctx: RunContext) -> Dict[str, Any]:
        """Run Agent P2: Relevance Filter"""
        logger.info("[P2] Filtering relevance for patents and news")
        
        # Get inputs from P1a and P1b
        patents_node = self.dag.nodes['p1a_patents']
        news_node = self.dag.nodes['p1b_news']
        
        patents: List[Patent] = patents_node.result.get('patents', [])
        articles: List[NewsArticle] = news_node.result.get('articles', [])
        
        if ctx.is_dry_run:
            logger.info("[P2] Dry run mode - skipping relevance filtering")
            return {'relevant_patents': [], 'relevant_news': [], 'count': 0}
        
        try:
            # Filter patents and news with bounded concurrency
            all_items = patents + articles
            ctx.increment('p2_items_total', len(all_items))
            
            results = []
            with ThreadPoolExecutor(max_workers=self.config.P2_CONCURRENCY) as executor:
                futures = [executor.submit(self.p2_agent.classify, item) for item in all_items]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        ctx.increment('p2_items_classified', 1)
                    except Exception as e:
                        logger.warning(f"[P2] Classification failed for item: {e}")
                        ctx.add_error('p2_relevance', str(e))
                        if self.config.DLQ_ENABLED:
                            # DLQ write would need item context - skipping for now
                            pass
            
            # Persist relevance results
            persist_result = self.storage.persist_relevance(results)
            ctx.increment('p2_results_persisted', persist_result.get('count', 0))
            
            # Filter relevant items
            relevant_count = sum(1 for r in results if r.is_relevant)
            ctx.increment('p2_relevant_items', relevant_count)
            
            logger.info(f"[P2] Classified {len(results)} items, {relevant_count} relevant")
            
            return {'results': results, 'count': len(results), 'relevant_count': relevant_count}
        
        except Exception as e:
            logger.error(f"[P2] Error: {e}", exc_info=True)
            ctx.add_error('p2_relevance', str(e))
            raise
    
    def _run_p3(self, ctx: RunContext) -> Dict[str, Any]:
        """Run Agent P3: Extraction & Classification"""
        logger.info("[P3] Extracting entities and sectors")
        
        # Get relevant items from P2
        p2_node = self.dag.nodes['p2_relevance']
        relevance_results = p2_node.result.get('results', [])
        
        # Get original items
        patents_node = self.dag.nodes['p1a_patents']
        news_node = self.dag.nodes['p1b_news']
        patents: List[Patent] = patents_node.result.get('patents', [])
        articles: List[NewsArticle] = news_node.result.get('articles', [])
        
        if ctx.is_dry_run:
            logger.info("[P3] Dry run mode - skipping extraction")
            return {'results': [], 'count': 0}
        
        try:
            # Filter to relevant items only
            relevant_item_ids = {r.item_id for r in relevance_results if r.is_relevant}
            
            relevant_patents = [p for p in patents if p.publication_number in relevant_item_ids]
            relevant_news = [a for a in articles if a.id in relevant_item_ids]
            
            all_relevant = relevant_patents + relevant_news
            ctx.increment('p3_items_total', len(all_relevant))
            
            logger.info(f"[P3] Processing {len(all_relevant)} relevant items")
            
            # Extract with bounded concurrency
            results = []
            with ThreadPoolExecutor(max_workers=self.config.P3_CONCURRENCY) as executor:
                futures = [executor.submit(self.p3_agent.extract, item) for item in all_relevant]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        ctx.increment('p3_items_extracted', 1)
                    except Exception as e:
                        logger.warning(f"[P3] Extraction failed for item: {e}")
                        ctx.add_error('p3_extraction', str(e))
            
            # Persist extraction results
            persist_result = self.storage.persist_extractions(results)
            ctx.increment('p3_results_persisted', persist_result.get('count', 0))
            
            logger.info(f"[P3] Extracted {len(results)} results")
            
            return {'results': results, 'count': len(results)}
        
        except Exception as e:
            logger.error(f"[P3] Error: {e}", exc_info=True)
            ctx.add_error('p3_extraction', str(e))
            raise
    
    def _run_p4(self, ctx: RunContext) -> Dict[str, Any]:
        """Run Agent P4: Entity Resolution"""
        logger.info("[P4] Resolving company entities")
        
        # Get company names from P3
        p3_node = self.dag.nodes['p3_extraction']
        extraction_results = p3_node.result.get('results', [])
        
        if ctx.is_dry_run:
            logger.info("[P4] Dry run mode - skipping entity resolution")
            return {'entities': [], 'aliases': [], 'count': 0}
        
        try:
            # Collect unique company names
            all_companies = []
            for result in extraction_results:
                all_companies.extend(result.company_names)
            
            unique_companies = list(set(all_companies))
            ctx.increment('p4_companies_total', len(unique_companies))
            
            logger.info(f"[P4] Resolving {len(unique_companies)} unique company names")
            
            # Resolve entities
            entities, aliases = self.p4_agent.resolve_batch(unique_companies)
            ctx.increment('p4_entities_resolved', len(entities))
            ctx.increment('p4_aliases_created', len(aliases))
            
            # Persist
            persist_result = self.storage.persist_entities(entities, aliases)
            
            if not persist_result.get('success'):
                raise Exception(f"Failed to persist entities: {persist_result}")
            
            logger.info(f"[P4] Resolved {len(entities)} entities with {len(aliases)} aliases")
            
            return {'entities': entities, 'aliases': aliases, 'count': len(entities)}
        
        except Exception as e:
            logger.error(f"[P4] Error: {e}", exc_info=True)
            ctx.add_error('p4_resolution', str(e))
            raise
    
    def run(self) -> RunContext:
        """
        Run the complete pipeline
        
        Returns:
            RunContext with execution statistics
        """
        # Create run context
        start_date, end_date = self.config.get_date_range()
        ctx = RunContext(
            run_mode=self.config.RUN_MODE,
            start_date=start_date,
            end_date=end_date,
            is_dry_run=self.config.is_dry_run()
        )
        
        logger.info(f"[Orchestrator] Starting run: {ctx.summary()}")
        
        try:
            # Execute DAG
            summary = self.dag.execute(ctx, fail_fast=False)
            
            # Log summary
            logger.info(f"[Orchestrator] Run complete: {ctx.summary()}")
            logger.info(f"[Orchestrator] Statistics: {ctx.stats}")
            
            if ctx.errors:
                logger.warning(f"[Orchestrator] {len(ctx.errors)} errors occurred:")
                for error in ctx.errors:
                    logger.warning(f"  - [{error['node']}] {error['message']}")
            
            return ctx
        
        except Exception as e:
            logger.error(f"[Orchestrator] Fatal error: {e}", exc_info=True)
            ctx.add_error('orchestrator', str(e))
            raise


def main():
    """CLI entrypoint"""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, OrchestratorConfig.LOG_LEVEL),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info("=" * 80)
    logger.info("Ballistic Intel Pipeline Orchestrator")
    logger.info("=" * 80)
    logger.info(f"Run Mode: {OrchestratorConfig.RUN_MODE}")
    logger.info(f"Date Range: {OrchestratorConfig.get_date_range()}")
    logger.info(f"Concurrency: P2={OrchestratorConfig.P2_CONCURRENCY}, P3={OrchestratorConfig.P3_CONCURRENCY}")
    logger.info(f"Dry Run: {OrchestratorConfig.is_dry_run()}")
    logger.info("=" * 80)
    
    try:
        orchestrator = PipelineOrchestrator()
        ctx = orchestrator.run()
        
        # Exit code based on errors
        exit_code = 0 if len(ctx.errors) == 0 else 1
        sys.exit(exit_code)
    
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

