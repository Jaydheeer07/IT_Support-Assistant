from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity

class AtlasTeamsBot(ActivityHandler):
    def __init__(self, agent, memory):
        self._agent = agent
        self._memory = memory

    async def on_message_activity(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        session_id = turn_context.activity.conversation.id
        user_message = (turn_context.activity.text or "").strip()

        if not user_message:
            return

        # Send typing indicator
        await turn_context.send_activity(Activity(type="typing"))

        response_text = await self._agent.respond(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
        )

        await turn_context.send_activity(response_text)

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome = (
                    "Hi! I'm **A.T.L.A.S.** — your IT support assistant.\n\n"
                    "I can help with common IT issues like:\n"
                    "- Clearing browser cookies\n"
                    "- Setting up email on a new device\n"
                    "- Accessing shared mailboxes\n"
                    "- Password resets\n\n"
                    "Just describe your issue and I'll guide you through it!"
                )
                await turn_context.send_activity(welcome)
