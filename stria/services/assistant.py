from __future__ import annotations

import json
import logging

from stria.models import AssistantRequest, AssistantResponse
from stria.services import llm_client
from stria.services.retrieval import store

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """\
You are a clinical support assistant embedded in the Stria RDT reader, used by both \
community health workers and licensed medical professionals.

IMPORTANT RULES:
- Always call search_documents before answering any clinical question.
- Never claim the result is a clinical diagnosis — it is a screening result.
- Keep answers concise (3–6 sentences).
- Calibrate your response to the apparent expertise of the user:
  * If the question uses clinical terminology or is clearly from a medical professional, \
answer at that level and do not add unsolicited referral caveats — they can make \
prescribing decisions themselves.
  * If the question suggests a non-professional user, use plain language and recommend \
following the protocol or referring to a health facility before any treatment.

CURRENT SCAN RESULT:
{scan_context_json}
"""

_FALLBACK_REPLY = (
    "I'm sorry, I'm unable to answer right now — the assistant service is temporarily unavailable. "
    "Please refer to the protocol steps shown on the result screen, or consult a health facility."
)


def respond(request: AssistantRequest) -> AssistantResponse:
    """
    Run the follow-up assistant with tool calling for document retrieval.
    Falls back to a static reply if both LLM providers fail.
    """
    scan_json = request.scan_context.model_dump_json(indent=2)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(scan_context_json=scan_json)

    # Build message history in OpenAI format
    messages: list[dict] = [
        {"role": msg.role, "content": msg.content}
        for msg in request.history
    ]
    messages.append({"role": "user", "content": request.message})

    def tool_handler(query: str) -> list[dict]:
        return store.search(query, top_k=3)

    cassette_type = request.scan_context.cassette_type
    outcome = request.scan_context.result.outcome
    logger.info(
        "assistant_turn | cassette=%s outcome=%s history_len=%d | user: %s",
        cassette_type, outcome, len(request.history), request.message[:300],
    )

    try:
        text, sources = llm_client.assistant_call(
            system_prompt=system_prompt,
            messages=messages,
            tool_handler=tool_handler,
            max_tool_calls=2,
        )
        reply = text or _FALLBACK_REPLY
        logger.info(
            "assistant_turn | cassette=%s outcome=%s sources=%s | assistant: %s",
            cassette_type, outcome, sources, reply[:300],
        )
        return AssistantResponse(message=reply, sources=sources)
    except llm_client.LLMUnavailableError:
        logger.error("Both LLM providers failed for assistant call")
        return AssistantResponse(message=_FALLBACK_REPLY, sources=[])
