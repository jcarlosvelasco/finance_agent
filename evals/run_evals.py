import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, cast

from evals.judge import evaluate_report
from evals.schema.BenchmarkRun import BenchmarkRun
from evals.schema.EvaluationResult import EvaluationResult

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
    initial_state: AnalysisState = {
        "ticker": ticker,
        "valid_ticker": False,
        "error": None,
        "company_info": None,
        "news_items": None,
        "sentiment": None,
        "key_events": None,
        "report": None,
        "evaluation": None,
    }
    result = await compiled.ainvoke(initial_state)
    return cast(AnalysisState, result)


async def evaluate_ticker(entry: dict) -> EvaluationResult:
    ticker = entry["ticker"]
    company_name = entry.get("company_name", ticker)
    sector = entry.get("sector", "")
    industry = entry.get("industry", "")
    notes = entry.get("notes", "")
    expected_sections = entry.get("expected_sections", [])

    logger.info(f"Running pipeline for {ticker}...")
    pipeline_start = time.monotonic()
    result = await run_pipeline_for_ticker(ticker)
    pipeline_duration = time.monotonic() - pipeline_start
    logger.info(f"Pipeline for {ticker} completed in {pipeline_duration:.1f}s")

    if result.get("error"):
        logger.error(f"Pipeline error for {ticker}: {result['error']}")
        return EvaluationResult(
            ticker=ticker,
            company_name=company_name,
            sector=sector,
            report_length_chars=0,
            report_sections_found=[],
            sections_expected=expected_sections,
            sections_coverage=0.0,
            dimensions=[],
            overall_score=0.0,
            error=f"Pipeline error: {result['error']}",
            has_report=False,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    report_text = result.get("report")
    if not report_text:
        return EvaluationResult(
            ticker=ticker,
            company_name=company_name,
            sector=sector,
            report_length_chars=0,
            report_sections_found=[],
            sections_expected=expected_sections,
            sections_coverage=0.0,
            dimensions=[],
            overall_score=0.0,
            error="No report generated",
            has_report=False,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    judge_result = await evaluate_report(
        ticker=ticker,
        company_name=company_name,
        sector=sector,
        industry=industry,
        notes=notes,
        report=report_text,
        company_info=result.get("company_info"),
        expected_sections=expected_sections,
    )

    judge_result.generated_at = datetime.now(timezone.utc).isoformat()
    return judge_result


async def run_benchmark(
    dataset_path: Optional[Path] = None, ticker_filter: Optional[List[str]] = None
) -> BenchmarkRun:
    dataset = load_golden_dataset(dataset_path)

    if ticker_filter:
        dataset = [item for item in dataset if item["ticker"].upper() in ticker_filter]
        logger.info(f"Filtered dataset to {len(dataset)} items: {ticker_filter}")

    results: List[EvaluationResult] = []
    successful = 0
    failed = 0

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    for entry in dataset:
        ticker = entry["ticker"]
        try:
            eval_result = await evaluate_ticker(entry)
            results.append(eval_result)
            if eval_result.error:
                failed += 1
                logger.warning(f"{ticker}: FAILED - {eval_result.error}")
            else:
                successful += 1
                logger.info(
                    f"{ticker}: score={eval_result.overall_score}, "
                    f"coverage={eval_result.sections_coverage:.0%}"
                )
        except Exception as e:
            failed += 1
            logger.error(f"{ticker}: ERROR - {str(e)}")
            results.append(
                EvaluationResult(
                    ticker=ticker,
                    company_name=entry.get("company_name", ticker),
                    sector=entry.get("sector", ""),
                    report_length_chars=0,
                    report_sections_found=[],
                    sections_expected=entry.get("expected_sections", 0),
                    sections_coverage=0.0,
                    dimensions=[],
                    overall_score=0.0,
                    error=f"Unexpected error: {e}",
                    has_report=False,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                )
            )

    valid_results = [r for r in results if not r.error]
    avg_overall = (
        sum(r.overall_score for r in valid_results) / len(valid_results)
        if valid_results
        else 0.0
    )
    avg_coverage = (
        sum(r.sections_coverage for r in valid_results) / len(valid_results)
        if valid_results
        else 0.0
    )

    avg_dimension_scores: dict[str, float] = {}
    if valid_results:
        dim_map: dict[str, list[float]] = {}
        for r in valid_results:
            for d in r.dimensions:
                dim_map.setdefault(d.name, []).append(float(d.score))

        for name, scores in dim_map.items():
            avg_dimension_scores[name] = round(sum(scores) / len(scores), 2)

    run = BenchmarkRun(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_tickers=len(dataset),
        successful=successful,
        failed=failed,
        avg_overall_score=round(avg_overall, 2),
        avg_section_coverage=round(avg_coverage, 2),
        avg_dimension_scores=avg_dimension_scores,
        results=results,
        metadata={
            "ticker_filter": ticker_filter,
            "dataset_path": str(dataset_path or GOLDEN_DATASET_PATH),
        },
    )

    save_results(run, run_id)

    return run


def save_results(run: BenchmarkRun, run_id: str) -> Path:
    if not RESULTS_DIR.exists():
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    result_path = RESULTS_DIR / f"{run_id}.json"
    result_path.write_text(
        run.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )

    logger.info(f"Results saved to {result_path}")

    return result_path


if __name__ == "__main__":
    asyncio.run(run_benchmark())
