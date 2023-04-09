from Bard import Chatbot
import config


class Bard:
    def __init__(self, id=None) -> None:
        self.mode = "bard"
        self.client = Chatbot(config.bard_api)
        self.prompt = ""
        self.id = id
        self.HUMAN_PROMPT = "\n\nHuman:"
        self.AI_PROMPT = "\n\nAssistant:"

    def reset(self):
        self.prompt = ""

    def get_mode(self):
        return self.mode

    def send_message(self, message):
        self.prompt = f"{self.prompt}{self.HUMAN_PROMPT} {message}{self.AI_PROMPT}"
        response = self.client.ask(self.prompt)['content']
        self.prompt = f"{self.prompt} {response}"

        return response
