"""Core agent loop using OpenRouter (OpenAI-compatible API)."""

import json
from typing import Generator

from openai import OpenAI

from .prompts import SYSTEM_PROMPT
from .tools import TOOL_DEFINITIONS, execute_tool

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_MODEL = "anthropic/claude-sonnet-4-5"   # Claude Sonnet via OpenRouter
_MAX_TOKENS = 4096
_MAX_TOOL_ROUNDS = 10


def _make_client(api_key: str) -> OpenAI:
    return OpenAI(
        base_url=_OPENROUTER_BASE_URL,
        api_key=api_key,
    )


def run_agent(
    display_history: list[dict],
    user_prompt: str,
    bq_client,
    api_key: str,
    batch: str = "",
    semester: str = "",
) -> tuple[str, list[dict]]:
    """
    Run the agent with multi-step tool calling via OpenRouter.

    Returns:
        (final_text_response, tool_call_log)
    """
    client = _make_client(api_key)

    # Build message list from text-only display history
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in display_history:
        messages.append({"role": msg["role"], "content": str(msg["content"])})

    context_prefix = f"[Context: batch={batch}, semester={semester}]\n\n" if (batch or semester) else ""
    messages.append({"role": "user", "content": context_prefix + user_prompt})

    tool_call_log: list[dict] = []
    rounds = 0

    while rounds < _MAX_TOOL_ROUNDS:
        rounds += 1

        response = client.chat.completions.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        choice = response.choices[0]
        message = choice.message

        if choice.finish_reason == "stop":
            return message.content or "", tool_call_log

        elif choice.finish_reason == "tool_calls":
            # Add the assistant message (with tool_calls) to history
            tool_calls_serialised = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ]
            messages.append({
                "role": "assistant",
                "content": message.content,  # may be None or partial text
                "tool_calls": tool_calls_serialised,
            })

            # Execute each tool and add results
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                result = execute_tool(tc.function.name, args, bq_client)
                tool_call_log.append({"tool": tc.function.name, "input": args, "result": result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

        else:
            return f"Unexpected finish reason: {choice.finish_reason}", tool_call_log

    return "Reached maximum tool-call rounds. Please simplify your query.", tool_call_log


def run_agent_streaming(
    display_history: list[dict],
    user_prompt: str,
    bq_client,
    api_key: str,
    batch: str = "",
    semester: str = "",
) -> Generator[dict, None, None]:
    """
    Streaming variant — yields progress events for real-time UI updates.

    Event types:
        {"type": "tool_start",  "tool": name, "input": {...}}
        {"type": "tool_result", "tool": name, "result": {...}}
        {"type": "done",        "text": full_response}
        {"type": "error",       "message": "..."}
    """
    client = _make_client(api_key)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in display_history:
        messages.append({"role": msg["role"], "content": str(msg["content"])})

    context_prefix = f"[Context: batch={batch}, semester={semester}]\n\n" if (batch or semester) else ""
    messages.append({"role": "user", "content": context_prefix + user_prompt})

    rounds = 0

    while rounds < _MAX_TOOL_ROUNDS:
        rounds += 1

        try:
            response = client.chat.completions.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
        except Exception as exc:
            yield {"type": "error", "message": str(exc)}
            return

        choice = response.choices[0]
        message = choice.message

        if choice.finish_reason == "stop":
            yield {"type": "done", "text": message.content or ""}
            return

        elif choice.finish_reason == "tool_calls":
            tool_calls_serialised = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ]
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls_serialised,
            })

            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                yield {"type": "tool_start", "tool": tc.function.name, "input": args}
                result = execute_tool(tc.function.name, args, bq_client)
                yield {"type": "tool_result", "tool": tc.function.name, "result": result}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

        else:
            yield {"type": "error", "message": f"Unexpected finish reason: {choice.finish_reason}"}
            return

    yield {"type": "error", "message": "Max tool-call rounds reached."}
