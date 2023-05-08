from asyncio import get_event_loop

from Bard import Chatbot

from config import bard_api


class Bard:
    def __init__(self):
        self.client = Chatbot(bard_api)

    def reset(self):
        self.client.conversation_id = ''
        self.client.response_id = ''
        self.client.choice_id = ''

    async def send_message(self, message):
        return await get_event_loop().run_in_executor(None, self.client.ask, message)
