import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from src.graph.graph import graph
from src.graph.state import AnalysisState

logger = logging.getLogger(__name__)


def _load_env() -> None:
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("\"'")
        if key and not os.environ.get(key):
            os.environ[key] = val


_load_env()

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"

RESULTS_DIR = Path(__file__).parent / "results"


def load_golden_dataset(path: Optional[Path] = None) -> List[dict]:
    dataset_path = path or GOLDEN_DATASET_PATH
    if not dataset_path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {dataset_path}")
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(data)} entries from golden dataset")
    return data


async def run_pipeline_for_ticker(ticker: str) -> AnalysisState:
    compiled = graph.compile()
    initial_state = AnalysisState(ticker=ticker)
    result = await compiled.ainvoke(initial_state)
    return AnalysisState.model_validate(result)
