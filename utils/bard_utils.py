from Bard import Chatbot

from config import bard_api


class Bard:
    def __init__(self):
        self.client = Chatbot(bard_api)
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

    def send_message(self, message):
        self.prev_conversation_id = self.client.conversation_id
        self.prev_response_id = self.client.response_id
        self.prev_choice_id = self.client.choice_id
        response = self.client.ask(message)
        return response
