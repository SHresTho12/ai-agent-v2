import logging
from .cli import main as cli_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

def main():
    """Project entrypoint"""
    setup_logging()
    cli_main()

if __name__ == "__main__":
    main()
