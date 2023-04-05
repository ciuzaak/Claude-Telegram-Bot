import anthropic
import config


class Claude:
    def __init__(self, model="claude-v1.2", id=None) -> None:
        assert model in {"claude-v1", "claude-v1.2"}, f"Unkown model: {model}"
        self.model = model
        self.max_tokens_to_sample = 9216
        self.stop_sequences = [anthropic.HUMAN_PROMPT]
        self.client = anthropic.Client(config.claude_api)
        self.prompt = ""
        self.id = id

    def reset(self):
        self.prompt = ""
        self.max_tokens_to_sample = 9216

    def send_message(self, message):
        self.prompt = f"{self.prompt}{anthropic.HUMAN_PROMPT} {message}{anthropic.AI_PROMPT}"
        self.max_tokens_to_sample -= anthropic.count_tokens(self.prompt)
        response = self.client.completion(
            prompt=self.prompt,
            stop_sequences=self.stop_sequences,
            max_tokens_to_sample=self.max_tokens_to_sample,
            model=self.model,
        )
        self.prompt = f"{self.prompt}{response['completion']}"
        return response['completion']

    def send_message_stream(self, message):
        self.prompt = f"{self.prompt}{anthropic.HUMAN_PROMPT} {message}{anthropic.AI_PROMPT}"
        self.max_tokens_to_sample -= anthropic.count_tokens(self.prompt)
        response = self.client.completion_stream(
            prompt=self.prompt,
            stop_sequences=self.stop_sequences,
            max_tokens_to_sample=self.max_tokens_to_sample,
            model=self.model,
            stream=True
        )
        for data in response:
            yield data['completion']
        self.prompt = f"{self.prompt}{data['completion']}"
