from Bard import AsyncChatbot

from config import psid, psidts


class Bard:
    def __init__(self):
        self.client = AsyncChatbot(psid, psidts)
        self.prev_conversation_id = ""
        self.prev_response_id = ""
        self.prev_choice_id = ""

    def reset(self):
        self.client.conversation_id = ""
        self.client.response_id = ""
        self.client.choice_id = ""
        self.prev_conversation_id = ""
        self.prev_response_id = ""
        self.prev_choice_id = ""

    def revert(self):
        self.client.conversation_id = self.prev_conversation_id
        self.client.response_id = self.prev_response_id
        self.client.choice_id = self.prev_choice_id

    async def send_message(self, message):
        if not hasattr(self.client, "SNlM0e"):
            self.client.SNlM0e = await self.client._AsyncChatbot__get_snlm0e()
        self.prev_conversation_id = self.client.conversation_id
        self.prev_response_id = self.client.response_id
        self.prev_choice_id = self.client.choice_id
        response = await self.client.ask(message)
        return response
