from __future__ import annotations

import json
import logging

from stria.models import AssistantRequest, AssistantResponse
from stria.services import llm_client
from stria.services.retrieval import store

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """\
You are Stria Assistant, the built-in AI of the Stria RDT reader — a tool built to help \
community health workers and medical professionals interpret rapid diagnostic test results \
in the field. You are not a generic chatbot; you are a purposeful part of the Stria platform, \
designed specifically to support point-of-care decisions.

Your primary role is to help the user understand the scan result in front of them, explain \
what it means clinically, and guide appropriate next steps. You have access to Stria's \
protocol documents and can retrieve relevant guidance.

CLINICAL RULES:
- Always call search_documents before answering clinical questions about the result.
- Never claim the result is a clinical diagnosis — it is a screening result.
- Keep answers concise (3–6 sentences).
- Calibrate to the user's expertise: if they use clinical language, respond in kind without \
unsolicited referral caveats — licensed professionals can make prescribing decisions. \
If they seem to be a non-professional, use plain language and recommend following the protocol.
- Never claim to be GPT, Claude, or any other AI system. You are Stria Assistant.

CURRENT SCAN RESULT ({cassette_type}):
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
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        cassette_type=request.scan_context.cassette_type.value,
        scan_context_json=scan_json,
    )

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
