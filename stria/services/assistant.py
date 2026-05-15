from __future__ import annotations

import json
import logging

from stria.models import AssistantRequest, AssistantResponse
from stria.services import llm_client
from stria.services.retrieval import store

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """\
You are a clinical support assistant for community health workers using the Stria RDT reader.
You help health workers understand test results and what to do next.

IMPORTANT RULES:
- Always call search_documents before answering any clinical question.
- Use plain language — no unexplained medical jargon.
- Never tell the health worker to administer treatment — always refer to the protocol.
- Never claim the result is a clinical diagnosis.
- Keep answers concise (3–6 sentences).

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

    try:
        text, sources = llm_client.assistant_call(
            system_prompt=system_prompt,
            messages=messages,
            tool_handler=tool_handler,
            max_tool_calls=2,
        )
        return AssistantResponse(message=text or _FALLBACK_REPLY, sources=sources)
    except llm_client.LLMUnavailableError:
        logger.error("Both LLM providers failed for assistant call")
        return AssistantResponse(message=_FALLBACK_REPLY, sources=[])
