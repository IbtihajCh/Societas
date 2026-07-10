import sys
import logging

from models.router.vllm_router import VLLMRouter
from models.config import AIConfig
from models.evaluation.evaluate import run_evaluation_suite

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("societas.ai.evaluation.runner")


def main() -> int:
    logger.info("=== Evaluation Suite ===")
    router = VLLMRouter(AIConfig())
    results = run_evaluation_suite(router)

    passed = 0
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        mark = "\u2713" if r.passed else "\u2717"
        print(f"  {mark} {r.scenario} ({r.duration_ms:.1f}ms)")
        if r.passed:
            passed += 1

    total = len(results)
    total_ms = sum(r.duration_ms for r in results)
    print("-" * 50)
    print(f"Result: {passed}/{total} passed ({total_ms:.1f}ms total)")

    failed = [r for r in results if not r.passed]
    if failed:
        print("\nFailures:")
        for r in failed:
            print(f"  - {r.scenario}: {r.error or 'unexpected result'}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
