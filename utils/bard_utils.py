from Bard import Chatbot

from config import config


class Bard:
    def __init__(self):
        self.client = Chatbot(config.bard_api)

    def reset(self):
        self.client.conversation_id = ''
        self.client.response_id = ''
        self.client.choice_id = ''
