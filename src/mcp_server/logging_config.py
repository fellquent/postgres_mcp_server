import logging
import sys


def configure_logging(level: str) -> None:
    # root logger stays quiet — avoiding third-party libs
    logging.basicConfig(
        level=logging.WARNING,
        stream=sys.stderr,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # level from config
    logging.getLogger("mcp_server").setLevel(level)