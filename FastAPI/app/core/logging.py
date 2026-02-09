import logging

def setup_logging(level: str = "INFO") -> None:
    # Простой единый формат логов для приложения
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
