from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import Anthropic
from openai import OpenAI

from stria.config import get_settings

logger = logging.getLogger(__name__)

OPENAI_VISION_MODEL = "gpt-4o"
OPENAI_ASSISTANT_MODEL = "gpt-4o"
CLAUDE_VISION_MODEL = "claude-sonnet-4-6"
CLAUDE_ASSISTANT_MODEL = "claude-sonnet-4-6"


class LLMUnavailableError(Exception):
    pass


def _openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def _anthropic_client() -> Anthropic:
    settings = get_settings()
    return Anthropic(api_key=settings.anthropic_api_key)


# ---------------------------------------------------------------------------
# Vision call — structured output (LineReading schema)
# ---------------------------------------------------------------------------

LINE_READING_SCHEMA = {
    "type": "object",
    "properties": {
        "control_line_present": {"type": "boolean"},
        "test_line_present": {"type": "boolean"},
        "test_line_intensity": {"type": "string", "enum": ["strong", "faint", "absent"]},
        "confidence": {"type": "number"},
        "raw_observation": {"type": "string"},
    },
    "required": [
        "control_line_present",
        "test_line_present",
        "test_line_intensity",
        "confidence",
        "raw_observation",
    ],
    "additionalProperties": False,
}


def vision_call(image_b64: str, system_prompt: str, user_prompt: str) -> dict:
    """
    Call the vision LLM and return a parsed LineReading dict.
    Tries OpenAI first; falls back to Claude on any exception.
    Raises LLMUnavailableError if both fail.
    """
    try:
        return _openai_vision(image_b64, system_prompt, user_prompt)
    except Exception as exc:
        logger.warning("OpenAI vision call failed (%s), trying Claude", exc)

    try:
        return _claude_vision(image_b64, system_prompt, user_prompt)
    except Exception as exc:
        logger.error("Claude vision call also failed: %s", exc)
        raise LLMUnavailableError("Both LLM providers unavailable for vision call") from exc


def _openai_vision(image_b64: str, system_prompt: str, user_prompt: str) -> dict:
    client = _openai_client()
    response = client.chat.completions.create(
        model=OPENAI_VISION_MODEL,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "line_reading",
                "schema": LINE_READING_SCHEMA,
                "strict": True,
            },
        },
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                    {"type": "text", "text": user_prompt},
                ],
            },
        ],
        max_tokens=512,
    )
    return json.loads(response.choices[0].message.content)


def _claude_vision(image_b64: str, system_prompt: str, user_prompt: str) -> dict:
    client = _anthropic_client()
    response = client.messages.create(
        model=CLAUDE_VISION_MODEL,
        max_tokens=512,
        system=system_prompt,
        tools=[
            {
                "name": "return_result",
                "description": "Return the structured line reading observation.",
                "input_schema": LINE_READING_SCHEMA,
            }
        ],
        tool_choice={"type": "any"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        ],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "return_result":
            return block.input
    raise ValueError("Claude did not return a tool_use block for return_result")


# ---------------------------------------------------------------------------
# Assistant call — function/tool calling with search_documents
# ---------------------------------------------------------------------------

SEARCH_TOOL_OPENAI = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": (
            "Search clinical guidelines for information relevant to this question. "
            "Expand the user's query using medical terminology and context from the scan result and conversation. "
            "Always call this before answering any clinical question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Expanded clinical search query using medical terminology",
                }
            },
            "required": ["query"],
        },
    },
}

SEARCH_TOOL_CLAUDE = {
    "name": "search_documents",
    "description": (
        "Search clinical guidelines for information relevant to this question. "
        "Expand the user's query using medical terminology and context from the scan result. "
        "Always call this before answering any clinical question."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Expanded clinical search query using medical terminology",
            }
        },
        "required": ["query"],
    },
}


def assistant_call(
    system_prompt: str,
    messages: list[dict],
    tool_handler: Any,
    max_tool_calls: int = 2,
) -> tuple[str, list[str]]:
    """
    Run an assistant conversation with tool calling.
    tool_handler(query: str) -> list[dict] is called when the model invokes search_documents.
    Returns (response_text, list_of_source_titles).
    Raises LLMUnavailableError if both providers fail.
    """
    try:
        return _openai_assistant(system_prompt, messages, tool_handler, max_tool_calls)
    except Exception as exc:
        logger.warning("OpenAI assistant call failed (%s), trying Claude", exc)

    try:
        return _claude_assistant(system_prompt, messages, tool_handler, max_tool_calls)
    except Exception as exc:
        logger.error("Claude assistant call also failed: %s", exc)
        raise LLMUnavailableError("Both LLM providers unavailable for assistant call") from exc


def _openai_assistant(
    system_prompt: str,
    messages: list[dict],
    tool_handler: Any,
    max_tool_calls: int,
) -> tuple[str, list[str]]:
    client = _openai_client()
    sources: list[str] = []
    tool_calls_made = 0

    chat_messages = [{"role": "system", "content": system_prompt}] + messages

    # max_tool_calls tool turns + 1 final answer turn = tight upper bound, no infinite loop
    for _ in range(max_tool_calls + 1):
        response = client.chat.completions.create(
            model=OPENAI_ASSISTANT_MODEL,
            tools=[SEARCH_TOOL_OPENAI],
            tool_choice="auto",
            messages=chat_messages,
            max_tokens=600,
        )
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" and tool_calls_made < max_tool_calls:
            tool_calls_made += 1
            tc = choice.message.tool_calls[0]
            args = json.loads(tc.function.arguments)
            results = tool_handler(args["query"])
            sources.extend(r["source"] for r in results if r.get("source") not in sources)

            chat_messages.append(choice.message)
            chat_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps([{"text": r["text"], "source": r["source"]} for r in results]),
            })
        else:
            return choice.message.content or "", sources

    raise ValueError(f"OpenAI assistant did not produce a text response after {max_tool_calls} tool calls")


def _claude_assistant(
    system_prompt: str,
    messages: list[dict],
    tool_handler: Any,
    max_tool_calls: int,
) -> tuple[str, list[str]]:
    client = _anthropic_client()
    sources: list[str] = []
    tool_calls_made = 0

    claude_messages = list(messages)

    # max_tool_calls tool turns + 1 final answer turn = tight upper bound, no infinite loop
    for _ in range(max_tool_calls + 1):
        response = client.messages.create(
            model=CLAUDE_ASSISTANT_MODEL,
            max_tokens=600,
            system=system_prompt,
            tools=[SEARCH_TOOL_CLAUDE],
            tool_choice={"type": "auto"},
            messages=claude_messages,
        )

        tool_use_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )

        if tool_use_block and tool_calls_made < max_tool_calls:
            tool_calls_made += 1
            results = tool_handler(tool_use_block.input["query"])
            sources.extend(r["source"] for r in results if r.get("source") not in sources)

            claude_messages.append({"role": "assistant", "content": response.content})
            claude_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": json.dumps(
                            [{"text": r["text"], "source": r["source"]} for r in results]
                        ),
                    }
                ],
            })
        else:
            text_block = next(
                (b for b in response.content if hasattr(b, "text")), None
            )
            return (text_block.text if text_block else ""), sources

    raise ValueError(f"Claude assistant did not produce a text response after {max_tool_calls} tool calls")
