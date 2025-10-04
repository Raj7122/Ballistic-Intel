"""
CLI Entrypoint for Pipeline Orchestrator
Run with: python -m pipeline [--mode MODE] [--lookback DAYS]
"""
import argparse
import sys
import os

# Set up orchestrator as main module
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ballistic Intel Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Incremental run (last 2 days)
  python -m pipeline --mode incremental --lookback 2
  
  # Backfill specific date range
  python -m pipeline --mode backfill --start 2024-12-01 --end 2024-12-07
  
  # Dry run (no external side effects)
  python -m pipeline --mode dry_run
  
  # With live integration tests
  LIVE_INTEGRATION=true python -m pipeline --mode incremental
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['incremental', 'backfill', 'dry_run'],
        default='incremental',
        help='Run mode (default: incremental)'
    )
    
    parser.add_argument(
        '--lookback',
        type=int,
        help='Lookback days for incremental mode (default: 2)'
    )
    
    parser.add_argument(
        '--start',
        help='Start date for backfill mode (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end',
        help='End date for backfill mode (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--p2-concurrency',
        type=int,
        help='Concurrency for P2 relevance filtering (default: 4)'
    )
    
    parser.add_argument(
        '--p3-concurrency',
        type=int,
        help='Concurrency for P3 extraction (default: 4)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set environment variables from CLI args
    os.environ['RUN_MODE'] = args.mode
    
    if args.lookback:
        os.environ['LOOKBACK_DAYS'] = str(args.lookback)
    
    if args.start:
        os.environ['START_DATE'] = args.start
    
    if args.end:
        os.environ['END_DATE'] = args.end
    
    if args.p2_concurrency:
        os.environ['P2_CONCURRENCY'] = str(args.p2_concurrency)
    
    if args.p3_concurrency:
        os.environ['P3_CONCURRENCY'] = str(args.p3_concurrency)
    
    os.environ['LOG_LEVEL'] = args.log_level
    
    # Import and run orchestrator (after env vars set)
    from orchestrator.runner import main
    main()

