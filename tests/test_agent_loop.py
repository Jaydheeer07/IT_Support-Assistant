import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from agent.loop import AtlasAgent

@pytest.fixture
def mock_tools():
    tools = MagicMock()
    tools.dispatch = AsyncMock(return_value='{"found": true, "results": [{"content": "Clear cookies: Settings > Privacy", "source": "clear-cookies", "confidence": 0.85}]}')
    return tools

@pytest.fixture
def mock_memory():
    mem = MagicMock()
    mem.get.return_value = []
    mem.save = MagicMock()
    return mem

@pytest.mark.asyncio
async def test_agent_returns_string_response(mock_tools, mock_memory):
    with patch("agent.loop.litellm.acompletion") as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(
                content="Here's how to clear your cookies...",
                tool_calls=None,
            ))]
        )
        agent = AtlasAgent(tools=mock_tools, memory=mock_memory)
        response = await agent.respond(
            session_id="s1", user_id="u1",
            user_message="How do I clear cookies?"
        )
        assert isinstance(response, str)
        assert len(response) > 0

@pytest.mark.asyncio
async def test_agent_calls_tool_when_llm_requests_it(mock_tools, mock_memory):
    with patch("agent.loop.litellm.acompletion") as mock_llm:
        tool_call = MagicMock()
        tool_call.function.name = "search_knowledge_base"
        tool_call.function.arguments = json.dumps({"query": "clear cookies"})
        tool_call.id = "call_123"

        # Mock model_dump() on tool_call for message serialization
        tool_call.model_dump.return_value = {
            "id": "call_123",
            "function": {"name": "search_knowledge_base", "arguments": json.dumps({"query": "clear cookies"})},
            "type": "function"
        }

        # First call: LLM requests tool use
        mock_llm.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(
                content=None, tool_calls=[tool_call]
            ))]),
            # Second call: LLM gives final answer
            MagicMock(choices=[MagicMock(message=MagicMock(
                content="Here are the steps to clear cookies...",
                tool_calls=None,
            ))]),
        ]
        agent = AtlasAgent(tools=mock_tools, memory=mock_memory)
        response = await agent.respond(
            session_id="s1", user_id="u1",
            user_message="Clear my cookies"
        )
        mock_tools.dispatch.assert_called_once_with(
            "search_knowledge_base", {"query": "clear cookies"},
            user_id="u1", session_id="s1"
        )
        assert isinstance(response, str)

@pytest.mark.asyncio
async def test_agent_saves_conversation_to_memory(mock_tools, mock_memory):
    with patch("agent.loop.litellm.acompletion") as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(
                content="Password reset steps...",
                tool_calls=None,
            ))]
        )
        agent = AtlasAgent(tools=mock_tools, memory=mock_memory)
        await agent.respond(session_id="s1", user_id="u1", user_message="Reset my password")
        mock_memory.save.assert_called_once()
