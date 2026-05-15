#!/usr/bin/env python
"""
Feed a single local image through the Stria pipeline and print results.

Usage:
    poetry run python scripts/test_image.py <image_path> [--type malaria] [--save-window]

Arguments:
    image_path          Path to a cassette photo (JPEG, PNG, or WEBP)
    --type, -t          Cassette type: malaria | covid | pregnancy | hiv  (default: malaria)
    --save-window, -s   Save the cropped result window as debug_window.jpg next to this script
    --brand, -b         Cassette brand for profile lookup (default: default)

Examples:
    poetry run python scripts/test_image.py photos/test1.jpg
    poetry run python scripts/test_image.py photos/sd_bioline.jpg --type malaria --brand sd_bioline --save-window
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time

# Ensure the repo root is on the path when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from stria.config import get_settings
from stria.models import CassetteType
from stria.services import imaging, protocols, vision
from stria.services.llm_client import LLMUnavailableError
from stria.utils.image import validate_image_size


SEP = "─" * 60


def _label(text: str) -> str:
    return f"\033[1m{text}\033[0m"  # bold


def _colour(text: str, outcome: str) -> str:
    codes = {"positive": "\033[91m", "negative": "\033[92m", "invalid": "\033[93m"}
    reset = "\033[0m"
    return f"{codes.get(outcome, '')}{text}{reset}"


def _bar(value: float, width: int = 30) -> str:
    filled = int(value * width)
    return "█" * filled + "░" * (width - filled)


async def run(image_path: str, cassette_type: CassetteType, brand: str, save_window: bool) -> None:
    settings = get_settings()

    print(f"\n{SEP}")
    print(f"  Stria — RDT pipeline test")
    print(f"  Image       : {image_path}")
    print(f"  Cassette    : {cassette_type.value}  brand={brand}")
    print(SEP)

    # ── Load image ──────────────────────────────────────────────────────────
    if not os.path.isfile(image_path):
        print(f"\n  ERROR: file not found: {image_path}")
        sys.exit(1)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    try:
        validate_image_size(image_bytes, max_mb=settings.max_image_size_mb)
    except ValueError as exc:
        print(f"\n  ERROR: {exc}")
        sys.exit(1)

    # ── Step 1: Quality ──────────────────────────────────────────────────────
    t0 = time.perf_counter()
    quality = imaging.assess_quality(image_bytes)
    print(f"\n[1] Quality assessment  ({_ms(t0)})")
    print(f"    Blur score  : {quality.blur_score:.1f}  (threshold ≥ {settings.blur_variance_threshold})")
    print(f"    Exposure OK : {quality.exposure_ok}")
    print(f"    Acceptable  : {quality.acceptable}")
    if not quality.acceptable:
        print(f"\n  ✗ HALTED — {quality.failure_reason.value}")
        print(f"    Fix: {_quality_fix(quality.failure_reason)}\n")
        sys.exit(0)

    # ── Step 2: Detect cassette ──────────────────────────────────────────────
    t0 = time.perf_counter()
    bbox = imaging.detect_cassette(image_bytes)
    print(f"\n[2] Cassette detection  ({_ms(t0)})")
    if bbox is None:
        print("    ✗ HALTED — no cassette shape detected")
        print("    Fix: ensure the full cassette is visible with clear edges")
        print("         and the background contrasts with the cassette body.\n")
        sys.exit(0)
    print(f"    Bounding box: x={bbox.x} y={bbox.y} w={bbox.w} h={bbox.h}")

    # ── Step 3: Extract result window ────────────────────────────────────────
    t0 = time.perf_counter()
    window = imaging.extract_result_window(image_bytes, bbox, cassette_type, brand=brand)
    print(f"\n[3] Result window crop  ({_ms(t0)})")
    print(f"    Window size : {window.shape[1]}×{window.shape[0]} px (w×h)")

    if save_window:
        import cv2
        out_path = os.path.join(os.path.dirname(__file__), "debug_window.jpg")
        cv2.imwrite(out_path, window)
        print(f"    Saved       : {out_path}")

    # ── Step 4: Vision LLM ──────────────────────────────────────────────────
    print(f"\n[4] Vision LLM call …")
    t0 = time.perf_counter()
    try:
        line_reading = await asyncio.to_thread(vision.interpret, window, cassette_type)
        elapsed = _ms(t0)
        print(f"    Done  ({elapsed})")
    except LLMUnavailableError:
        print("    ✗ HALTED — both LLM providers unavailable")
        print("    Check OPENAI_API_KEY and ANTHROPIC_API_KEY in your .env\n")
        sys.exit(1)
    except ValueError as exc:
        print(f"    ✗ HALTED — vision response parse failed: {exc}\n")
        sys.exit(1)

    # ── Line reading ─────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print(f"  Line Reading")
    print(SEP)
    c = "✓" if line_reading.control_line_present else "✗"
    t = "✓" if line_reading.test_line_present else "✗"
    print(f"    Control (C) : {c}  {'present' if line_reading.control_line_present else 'absent'}")
    print(f"    Test (T)    : {t}  {line_reading.test_line_intensity}")
    conf_pct = line_reading.confidence * 100
    print(f"    Confidence  : {_bar(line_reading.confidence)} {conf_pct:.0f}%")
    print(f"\n    AI observed : \"{line_reading.raw_observation}\"")

    # ── Derive outcome ───────────────────────────────────────────────────────
    if line_reading.confidence < settings.min_confidence:
        outcome = "invalid"
        invalid_reason = "result_ambiguous"
    elif not line_reading.control_line_present:
        outcome = "invalid"
        invalid_reason = "no_control_line"
    elif line_reading.test_line_present:
        outcome = "positive"
        invalid_reason = None
    else:
        outcome = "negative"
        invalid_reason = None

    # ── Step 5: Protocol lookup ──────────────────────────────────────────────
    protocol = protocols.lookup(cassette_type, outcome)

    # ── Final result ─────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    outcome_display = _colour(f"  RESULT: {outcome.upper()}", outcome)
    if invalid_reason:
        outcome_display += f"  ({invalid_reason})"
    print(outcome_display)
    print(SEP)

    if protocol:
        print(f"\n  Protocol: {protocol['title']}")
        print(f"  Refer   : {'YES — send to clinic' if protocol.get('refer') else 'No'}")
        print(f"\n  Steps:")
        for i, step in enumerate(protocol.get("steps", []), 1):
            print(f"    {i}. {step}")

    # ── Confidence warning ───────────────────────────────────────────────────
    if line_reading.confidence < settings.min_confidence:
        print(f"\n  ⚠  Confidence {conf_pct:.0f}% is below threshold ({settings.min_confidence * 100:.0f}%).")
        print(f"     Repeat the test with better lighting or a steadier hand.")
    elif line_reading.test_line_intensity == "faint":
        print(f"\n  ⚠  Faint T line detected. This is still a POSITIVE result.")
        print(f"     Do not dismiss a faint line as negative.")

    print(f"\n{SEP}\n")


def _ms(t0: float) -> str:
    return f"{(time.perf_counter() - t0) * 1000:.0f} ms"


def _quality_fix(reason) -> str:
    from stria.models import QualityFailure
    fixes = {
        QualityFailure.TOO_BLURRY: "Hold the phone steady and ensure autofocus has locked.",
        QualityFailure.TOO_DARK: "Move to better lighting or turn on the phone torch.",
        QualityFailure.TOO_BRIGHT: "Avoid direct sunlight or flash directly on the cassette.",
        QualityFailure.CASSETTE_NOT_FOUND: "Could not decode the image bytes.",
        QualityFailure.RESULT_WINDOW_OBSCURED: "Ensure nothing covers the result window.",
    }
    return fixes.get(reason, "Check image and retry.")


PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "photos")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _pick_image(given: str | None) -> str:
    if given:
        return given

    # Auto-discover from photos/
    candidates = sorted(
        f for f in os.listdir(PHOTOS_DIR)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    ) if os.path.isdir(PHOTOS_DIR) else []

    if not candidates:
        print("\n  No image given and photos/ is empty.")
        print("  Drop a cassette photo into photos/ then re-run, or pass a path directly:\n")
        print("    poetry run python scripts/test_image.py photos/cassette.jpg\n")
        sys.exit(1)

    if len(candidates) == 1:
        path = os.path.join(PHOTOS_DIR, candidates[0])
        print(f"\n  Auto-selected: {candidates[0]}")
        return path

    # Multiple files — let the user pick
    print(f"\n  Found {len(candidates)} photos in photos/:\n")
    for i, name in enumerate(candidates, 1):
        print(f"    [{i}] {name}")
    print()
    while True:
        choice = input("  Pick a number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            return os.path.join(PHOTOS_DIR, candidates[int(choice) - 1])
        print("  Invalid choice, try again.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Feed a cassette photo through the Stria pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Path to image file (JPEG/PNG/WEBP). Omit to pick from photos/",
    )
    parser.add_argument(
        "--type", "-t",
        dest="cassette_type",
        default="malaria",
        choices=[e.value for e in CassetteType],
        help="Cassette type (default: malaria)",
    )
    parser.add_argument(
        "--brand", "-b",
        default="default",
        help="Cassette brand for profile lookup (default: default)",
    )
    parser.add_argument(
        "--save-window", "-s",
        action="store_true",
        help="Save cropped result window as scripts/debug_window.jpg",
    )
    args = parser.parse_args()

    image_path = _pick_image(args.image)

    protocols.warm_cache()
    asyncio.run(run(image_path, CassetteType(args.cassette_type), args.brand, args.save_window))


if __name__ == "__main__":
    main()
