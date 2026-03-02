"""
Nightly learning processor.
Analyzes negative feedback and proposes memory.md additions for admin review.

Run via cron: 0 2 * * * cd /app && python -m learning.processor
"""
import json
from collections import defaultdict
from learning.feedback_store import FeedbackStore

MIN_NEGATIVE_THRESHOLD = 3  # Minimum negatives before triggering analysis


def run(feedback_db: str = "./learning/feedback.db",
        min_negative_threshold: int = MIN_NEGATIVE_THRESHOLD) -> int:
    """Analyze feedback and create proposals. Returns number of proposals created."""
    store = FeedbackStore(db_path=feedback_db)
    negatives = store.get_negative_feedback()

    if len(negatives) < min_negative_threshold:
        print(
            f"Only {len(negatives)} negative feedback entries "
            f"(threshold: {min_negative_threshold}). Nothing to propose."
        )
        return 0

    # Group by first 3 words of issue summary (simple keyword clustering for v1)
    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for entry in negatives:
        summary = (entry.get("issue_summary") or "unknown issue").lower()
        key = " ".join(summary.split()[:3])
        groups[key].append(entry)

    proposals_created = 0
    for group_key, entries in groups.items():
        if len(entries) < 2:
            continue
        session_ids = [e["session_id"] for e in entries]
        heuristic = (
            f"Pattern detected ({len(entries)} unresolved cases): "
            f"Users reporting issues related to '{group_key}' were not satisfied. "
            f"Consider adding or improving the knowledge base guide for this topic. "
            f"Review sessions: {', '.join(session_ids[:5])}"
        )
        store.add_proposal(heuristic=heuristic, session_ids=session_ids)
        print(f"  Proposal created for: '{group_key}' ({len(entries)} entries)")
        proposals_created += 1

    return proposals_created


if __name__ == "__main__":
    print("Running A.T.L.A.S. nightly learning processor...")
    count = run()
    print(f"Done. {count} proposal(s) created.")
