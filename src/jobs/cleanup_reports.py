import logging
import time
from datetime import date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"
INTERVAL_SECONDS = 24 * 60 * 60  # 24 horas


def cleanup():
    if not REPORTS_DIR.exists():
        logger.info("Reports dir does not exist, skipping")
        return

    today = date.today().isoformat()
    deleted = 0

    for path in REPORTS_DIR.glob("*.json"):
        # Formato: NVDA_2026-05-29.json — la fecha es lo que hay tras el _
        parts = path.stem.split("_", 1)
        if len(parts) != 2:
            continue
        file_date = parts[1]
        if file_date != today:
            path.unlink()
            logger.info(f"Deleted old report: {path.name}")
            deleted += 1

    logger.info(f"Cleanup complete — {deleted} files deleted")


if __name__ == "__main__":
    logger.info("Report cleanup job started")
    while True:
        cleanup()
        logger.info(f"Next cleanup in {INTERVAL_SECONDS // 3600}h")
        time.sleep(INTERVAL_SECONDS)
