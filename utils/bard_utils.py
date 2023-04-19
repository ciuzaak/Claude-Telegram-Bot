from Bard import Chatbot

from config import config


class Bard:
    def __init__(self, id=None) -> None:
        self.mode = "bard"
        self.client = Chatbot(config.bard_api)
        self.id = id

    def reset(self):
        self.client.conversation_id = ""
        self.client.response_id = ""
        self.client.choice_id = ""

    def get_mode(self):
        return self.mode

    def send_message(self, message):
        return self.client.ask(message)
