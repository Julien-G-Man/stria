from __future__ import annotations

import logging

import numpy as np

from stria.models import CassetteType, LineReading
from stria.services import llm_client
from stria.services.imaging import encode_for_vision

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert RDT (Rapid Diagnostic Test) line reader. "
    "You will be shown the result window of a rapid diagnostic test cassette. "
    "Your task is to identify whether a Control line (C) and a Test line (T) are present. "
    "Be especially attentive to faint lines — a faint T line is still a positive result. "
    "Never assume a line is absent unless you are certain. "
    "Return your observation in the required JSON format. "
    "Do not recommend treatment — only describe what you see."
)

_USER_PROMPT_TEMPLATE = (
    "This is the result window of a {cassette_type} rapid diagnostic test. "
    "Look carefully for:\n"
    "- A Control line (C) — usually the upper or lower labeled line\n"
    "- A Test line (T) — the line that indicates a positive result\n"
    "Even a very faint T line counts as present. "
    "Report your confidence as a decimal between 0.0 and 1.0. "
    "In raw_observation, describe exactly what you see in plain language."
)

_FALLBACK_READINGS: dict[str, dict] = {
    "cannot_read": {
        "control_line_present": False,
        "test_line_present": False,
        "test_line_intensity": "absent",
        "confidence": 0.0,
        "raw_observation": "Unable to interpret — vision service unavailable.",
    }
}


def interpret(window: np.ndarray, cassette_type: CassetteType) -> LineReading:
    """
    Send the cropped result window to the vision LLM and parse the response.
    Raises ValueError if the response cannot be parsed (pipeline will mark result_ambiguous).
    Raises llm_client.LLMUnavailableError if both providers fail.
    """
    image_b64 = encode_for_vision(window)
    user_prompt = _USER_PROMPT_TEMPLATE.format(cassette_type=cassette_type.value)

    raw = llm_client.vision_call(image_b64, _SYSTEM_PROMPT, user_prompt)

    # Validate required fields are present
    required = {"control_line_present", "test_line_present", "test_line_intensity", "confidence", "raw_observation"}
    missing = required - set(raw.keys())
    if missing:
        raise ValueError(f"Vision response missing fields: {missing}")

    # Clamp confidence
    raw["confidence"] = max(0.0, min(1.0, float(raw["confidence"])))

    # Normalise test_line_intensity
    if not raw.get("test_line_present"):
        raw["test_line_intensity"] = "absent"

    return LineReading(**raw)
