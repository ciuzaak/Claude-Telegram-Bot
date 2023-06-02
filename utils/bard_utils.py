from Bard import AsyncChatbot

from config import bard_api


class Bard:
    def __init__(self):
        self.client = AsyncChatbot(bard_api)
        self.client.SNlM0e = None
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
        if self.client.SNlM0e is None:
            self.client.SNlM0e = await self.client._AsyncChatbot__get_snlm0e()
        self.prev_conversation_id = self.client.conversation_id
        self.prev_response_id = self.client.response_id
        self.prev_choice_id = self.client.choice_id
        response = await self.client.ask(message)
        return response
