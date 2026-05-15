from __future__ import annotations

import json
import logging
from functools import lru_cache

from stria.config import get_settings
from stria.models import CassetteType

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_protocols() -> dict:
    settings = get_settings()
    with open(settings.protocols_path) as f:
        return json.load(f)


def lookup(cassette_type: CassetteType, outcome: str) -> dict | None:
    """
    Return the protocol dict for the given cassette type and outcome.
    Returns None if no protocol is defined — never raises.
    """
    try:
        protocols = _load_protocols()
        return protocols.get(cassette_type.value, {}).get(outcome)
    except Exception as exc:
        logger.error("Protocol lookup failed: %s", exc)
        return None


def warm_cache() -> None:
    """Call at startup to pre-load protocols.json into the lru_cache."""
    try:
        _load_protocols()
        logger.info("Protocols cache warmed")
    except Exception as exc:
        logger.error("Failed to warm protocols cache: %s", exc)
