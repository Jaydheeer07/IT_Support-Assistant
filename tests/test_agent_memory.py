import pytest
from unittest.mock import MagicMock
from agent.memory import SessionMemory

def test_get_returns_empty_list_for_new_session():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mem = SessionMemory(redis_client=mock_redis)
    result = mem.get("session-123")
    assert result == []

def test_save_and_get_messages():
    import json
    mock_redis = MagicMock()
    stored = {}
    mock_redis.set.side_effect = lambda k, v, ex=None: stored.update({k: v})
    mock_redis.get.side_effect = lambda k: stored.get(k)

    mem = SessionMemory(redis_client=mock_redis)
    messages = [{"role": "user", "content": "hello"}]
    mem.save("session-123", messages)
    result = mem.get("session-123")
    assert result == messages

def test_clear_removes_session():
    mock_redis = MagicMock()
    mem = SessionMemory(redis_client=mock_redis)
    mem.clear("session-123")
    mock_redis.delete.assert_called_once_with("atlas:session:session-123")

def test_append_adds_message_to_session():
    import json
    mock_redis = MagicMock()
    stored = {}
    mock_redis.set.side_effect = lambda k, v, ex=None: stored.update({k: v})
    mock_redis.get.side_effect = lambda k: stored.get(k)

    mem = SessionMemory(redis_client=mock_redis)
    mem.append("session-abc", "user", "Hello ATLAS")
    mem.append("session-abc", "assistant", "Hi! How can I help?")
    result = mem.get("session-abc")
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"
