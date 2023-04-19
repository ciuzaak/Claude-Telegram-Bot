import anthropic

from config import config


class Claude:
    def __init__(self, id=None) -> None:
        self.mode = 'claude'
        self.model = 'claude-v1.3'
        self.temperature = 1.
        self.max_tokens_to_sample = 9216
        self.stop_sequences = [anthropic.HUMAN_PROMPT]
        self.client = anthropic.Client(config.claude_api)
        self.prompt = ''
        self.id = id

    def reset(self):
        self.prompt = ''
        self.max_tokens_to_sample = 9216

    def get_mode(self):
        return self.mode

    def get_settings(self):
        return self.model, self.temperature

    def change_model(self, model):
        valid_models = {'claude-v1', 'claude-v1.0', 'claude-v1.2',
                        'claude-v1.3', 'claude-instant-v1', 'claude-instant-v1.0'}
        if model in valid_models:
            self.model = model
            return True
        return False

    def change_temperature(self, temperature):
        if not isinstance(temperature, float):
            try:
                temperature = float(temperature)
            except ValueError:
                return False

        if 0 <= temperature <= 1:
            self.temperature = temperature
            return True
        return False

    def send_message(self, message):
        self.prompt = f'{self.prompt}{anthropic.HUMAN_PROMPT} {message}{anthropic.AI_PROMPT}'
        self.max_tokens_to_sample -= anthropic.count_tokens(self.prompt)
        response = self.client.completion(
            prompt=self.prompt,
            stop_sequences=self.stop_sequences,
            max_tokens_to_sample=self.max_tokens_to_sample,
            model=self.model,
            temperature=self.temperature,
        )
        self.prompt = f"{self.prompt}{response['completion']}"
        return response['completion']

    def send_message_stream(self, message):
        self.prompt = f'{self.prompt}{anthropic.HUMAN_PROMPT} {message}{anthropic.AI_PROMPT}'
        self.max_tokens_to_sample -= anthropic.count_tokens(self.prompt)
        response = self.client.completion_stream(
            prompt=self.prompt,
            stop_sequences=self.stop_sequences,
            max_tokens_to_sample=self.max_tokens_to_sample,
            model=self.model,
            temperature=self.temperature,
            stream=True
        )
        for data in response:
            yield data['completion']
        self.prompt = f"{self.prompt}{data['completion']}"
