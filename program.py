#!/usr/bin/env python3
"""
TimeBars - Main Entry Point
A timer application with sequential timer queue and alarm notifications.
"""

import sys
import os
import logging
from pathlib import Path
from multiprocessing import freeze_support

# Set up basic logging early
_log_setup_done = False

def setup_logging() -> None:
    """Setup logging configuration."""
    global _log_setup_done
    if _log_setup_done:
        return
    _log_setup_done = True
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('timebars.log', mode='a', encoding='utf-8')
        ]
    )


def main() -> int:
    """Main entry point for TimeBars application."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check if this is the first run (not a subprocess reload)
    is_main = os.environ.get('TIMEBARS_SUBPROCESS') != '1'
    
    if is_main:
        os.environ['TIMEBARS_SUBPROCESS'] = '1'
    
    # Determine paths
    base_path = Path(__file__).parent.resolve()
    data_path = base_path / "data"
    
    if is_main:
        logger.info(f"Data path: {data_path}")
    
    # Ensure data directory exists
    data_path.mkdir(parents=True, exist_ok=True)
    
    # Import and run the app
    from scripts.interface import run_app
    
    # Run in native mode (Edge WebView via pywebview)
    run_app(data_path, native=True, port=8080)
    
    if is_main:
        logger.info("TimeBars closed")
    
    return 0


if __name__ == "__main__":
    freeze_support()  # Required for Windows multiprocessing
    
    try:
        sys.exit(main())
    except ImportError as e:
        setup_logging()
        logging.getLogger(__name__).error(f"Import error: {e}")
        print(f"\nError: {e}")
        print("Please run the installer first (Option 2 in the batch menu).")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        setup_logging()
        logging.getLogger(__name__).exception(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)