from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor

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
        with ThreadPoolExecutor() as executor:
            return await get_event_loop().run_in_executor(executor, self.client.ask, message)
