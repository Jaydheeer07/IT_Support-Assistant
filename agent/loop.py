import json
from pathlib import Path
import litellm
from agent.tools import ToolRegistry, TOOL_DEFINITIONS
from agent.memory import SessionMemory
import config

SOUL_PATH = Path(__file__).parent / "soul.md"
MEMORY_PATH = Path(__file__).parent / "memory.md"

REASONING_MODEL = "openrouter/anthropic/claude-haiku-4-5-20251001"
MAX_TOOL_ITERATIONS = 6


def _build_system_prompt() -> str:
    soul = SOUL_PATH.read_text(encoding="utf-8") if SOUL_PATH.exists() else ""
    memory = MEMORY_PATH.read_text(encoding="utf-8") if MEMORY_PATH.exists() else ""
    return f"{soul}\n\n## Operational Memory\n{memory}"


class AtlasAgent:
    def __init__(self, tools: ToolRegistry, memory: SessionMemory):
        self._tools = tools
        self._memory = memory
        self._system_prompt = _build_system_prompt()

    async def respond(self, session_id: str, user_id: str, user_message: str) -> str:
        messages = self._memory.get(session_id)

        # Add system prompt only on first message of a session
        if not messages:
            messages = [{"role": "system", "content": self._system_prompt}]

        messages.append({"role": "user", "content": user_message})

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await litellm.acompletion(
                model=REASONING_MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                api_key=config.OPENROUTER_API_KEY,
                api_base="https://openrouter.ai/api/v1",
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                # Final answer reached
                final_text = msg.content or ""
                messages.append({"role": "assistant", "content": final_text})
                self._memory.save(session_id, messages)
                return final_text

            # Process tool calls
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                result = await self._tools.dispatch(
                    tool_name, tool_args, user_id=user_id, session_id=session_id
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        # Max iterations reached — graceful fallback
        fallback = (
            "I've tried several approaches but wasn't able to fully resolve this. "
            "Let me create a support ticket for you so a human agent can follow up."
        )
        messages.append({"role": "assistant", "content": fallback})
        self._memory.save(session_id, messages)
        return fallback

    def reload_soul(self) -> None:
        """Reload soul.md and memory.md — call after admin approves a learning proposal."""
        self._system_prompt = _build_system_prompt()
