import pytest
import os
import tempfile
from learning.feedback_store import FeedbackStore

def test_record_feedback_stores_entry():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = None
    try:
        store = FeedbackStore(db_path=db_path)
        store.record(session_id="s1", user_id="u1", rating=1,
                     issue_summary="Couldn't clear cookies", resolved=True)
        entries = store.get_all()
        assert len(entries) == 1
        assert entries[0]["session_id"] == "s1"
        assert entries[0]["rating"] == 1
        assert entries[0]["resolved"] == 1
    finally:
        if store is not None:
            store.close()
        os.unlink(db_path)

def test_get_negative_feedback_filters_correctly():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = None
    try:
        store = FeedbackStore(db_path=db_path)
        store.record("s1", "u1", rating=1, issue_summary="Good resolution", resolved=True)
        store.record("s2", "u2", rating=-1, issue_summary="Shared mailbox still broken", resolved=False)
        negatives = store.get_negative_feedback()
        assert len(negatives) == 1
        assert negatives[0]["session_id"] == "s2"
        assert negatives[0]["rating"] == -1
    finally:
        if store is not None:
            store.close()
        os.unlink(db_path)

def test_add_and_get_pending_proposals():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = None
    try:
        store = FeedbackStore(db_path=db_path)
        proposal_id = store.add_proposal(
            heuristic="When user says 'permission denied on shared mailbox', ask if using legacy Outlook",
            session_ids=["s1", "s2"]
        )
        proposals = store.get_pending_proposals()
        assert len(proposals) == 1
        assert proposals[0]["id"] == proposal_id
        assert proposals[0]["status"] == "pending"
    finally:
        if store is not None:
            store.close()
        os.unlink(db_path)

def test_update_proposal_status():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = None
    try:
        store = FeedbackStore(db_path=db_path)
        pid = store.add_proposal("Test heuristic", ["s1"])
        store.update_proposal_status(pid, "approved")
        proposals = store.get_pending_proposals()
        assert len(proposals) == 0  # No more pending
    finally:
        if store is not None:
            store.close()
        os.unlink(db_path)
