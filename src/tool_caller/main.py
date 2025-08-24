import logging
from .cli import main as cli_main
from pathlib import Path
from .config.logging_config import setup_logging 

def main():
    """Project entrypoint"""

    # Then setup full logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting LLM Tool Caller...")
    
    
    cli_main()

if __name__ == "__main__":
    main()
