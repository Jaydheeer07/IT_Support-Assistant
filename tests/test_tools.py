import pytest
from unittest.mock import AsyncMock, MagicMock
from agent.tools import ToolRegistry, TOOL_DEFINITIONS

def test_tool_definitions_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        assert "type" in tool
        assert tool["type"] == "function"
        assert "function" in tool
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]

def test_tool_registry_lists_expected_tools():
    names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
    assert "search_knowledge_base" in names
    assert "search_web" in names
    assert "create_jira_ticket" in names
    assert "get_user_info" in names
    assert "escalate_to_human" in names

@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error():
    registry = ToolRegistry(kb=MagicMock(), jira=MagicMock(),
                             azure_ad=MagicMock(), brave=MagicMock())
    result = await registry.dispatch("nonexistent_tool", {}, user_id="u1", session_id="s1")
    assert "error" in result.lower()

@pytest.mark.asyncio
async def test_dispatch_search_knowledge_base_calls_kb():
    import json
    mock_kb = MagicMock()
    mock_kb.search.return_value = [{"content": "Clear cookies guide", "source": "cookies", "confidence": 0.9}]
    registry = ToolRegistry(kb=mock_kb, jira=MagicMock(), azure_ad=MagicMock(), brave=MagicMock())
    result = await registry.dispatch("search_knowledge_base", {"query": "clear cookies"}, user_id="u1", session_id="s1")
    data = json.loads(result)
    assert data["found"] is True
    assert len(data["results"]) == 1
    mock_kb.search.assert_called_once()
