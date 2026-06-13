import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="time=%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s",
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
