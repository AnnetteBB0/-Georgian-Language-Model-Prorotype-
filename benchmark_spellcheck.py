"""Small benchmark utility for Georgian spellcheck performance."""

from __future__ import annotations

import argparse
import statistics
import textwrap
import time
from pathlib import Path

from spellcheck import profile_spelling

DEFAULT_TEXT = textwrap.dedent(
    """
    გამარჯობა. ეს არის საცდელი ტექსტი ქართული მართლწერის შემმოწმებლისთვის.
    აქ არის სწორი სიტყვებიც და რამდენიმე შეცდომაც, მაგალითად ტექსტტ, შეცდომaa და
    გამარჯობაა. მიზანია ვნახოთ რამდენად სწრაფად ამოწმებს სისტემა მთელ აბზაცს.
    """
).strip()


def load_text(file_path: str | None) -> str:
    if not file_path:
        return DEFAULT_TEXT
    return Path(file_path).read_text(encoding="utf-8")


def merge_profiles(
    destination: dict[str, dict[str, float | int | str]],
    source_rows: list[dict[str, float | int | str]],
) -> None:
    for row in source_rows:
        word = str(row["word"])
        current = destination.setdefault(
            word,
            {
                "word": word,
                "occurrences": 0,
                "lookup_ms": 0.0,
                "suggest_ms": 0.0,
                "total_ms": 0.0,
                "mixed_script_hits": 0,
                "misspell_hits": 0,
                "suggestions_generated": 0,
            },
        )
        for key in (
            "occurrences",
            "lookup_ms",
            "suggest_ms",
            "total_ms",
            "mixed_script_hits",
            "misspell_hits",
            "suggestions_generated",
        ):
            current[key] += row[key]


def print_top_tokens(
    aggregated_profiles: dict[str, dict[str, float | int | str]],
    top_tokens: int,
) -> None:
    if top_tokens <= 0 or not aggregated_profiles:
        return

    print("top_tokens:")
    rows = sorted(
        aggregated_profiles.values(),
        key=lambda row: (float(row["total_ms"]), int(row["occurrences"])),
        reverse=True,
    )[:top_tokens]
    for row in rows:
        print(
            "  "
            f"{row['word']}: total_ms={float(row['total_ms']):.3f}, "
            f"lookup_ms={float(row['lookup_ms']):.3f}, "
            f"suggest_ms={float(row['suggest_ms']):.3f}, "
            f"occurrences={int(row['occurrences'])}, "
            f"mixed_script_hits={int(row['mixed_script_hits'])}, "
            f"misspell_hits={int(row['misspell_hits'])}, "
            f"suggestions_generated={int(row['suggestions_generated'])}"
        )


def run_benchmark(text: str, iterations: int, top_tokens: int) -> None:
    timings: list[float] = []
    last_annotations_count = 0
    aggregated_profiles: dict[str, dict[str, float | int | str]] = {}

    for _ in range(iterations):
        start = time.perf_counter()
        annotations, _, profile_rows = profile_spelling(text)
        timings.append((time.perf_counter() - start) * 1000)
        last_annotations_count = len(annotations)
        merge_profiles(aggregated_profiles, profile_rows)

    avg_ms = statistics.mean(timings)
    min_ms = min(timings)
    max_ms = max(timings)
    first_run_ms = timings[0]
    warm_avg_ms = statistics.mean(timings[1:]) if len(timings) > 1 else timings[0]

    print(f"characters={len(text)}")
    print(f"iterations={iterations}")
    print(f"annotations={last_annotations_count}")
    print(f"first_run_ms={first_run_ms:.2f}")
    print(f"warm_avg_ms={warm_avg_ms:.2f}")
    print(f"avg_ms={avg_ms:.2f}")
    print(f"min_ms={min_ms:.2f}")
    print(f"max_ms={max_ms:.2f}")
    print_top_tokens(aggregated_profiles, top_tokens)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the Georgian spellchecker.")
    parser.add_argument(
        "--file",
        help="UTF-8 text file to benchmark. If omitted, a built-in sample is used.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of repeated runs to execute.",
    )
    parser.add_argument(
        "--top-tokens",
        type=int,
        default=5,
        help="How many of the slowest tokens to print.",
    )
    args = parser.parse_args()

    text = load_text(args.file)
    run_benchmark(text, args.iterations, args.top_tokens)


if __name__ == "__main__":
    main()
