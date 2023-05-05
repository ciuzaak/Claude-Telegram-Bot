from anthropic import AI_PROMPT, HUMAN_PROMPT, Client, count_tokens

from config import claude_api


class Claude:
    def __init__(self):
        self.model = 'claude-v1.3'
        self.temperature = 1.
        self.cutoff = 50
        self.max_tokens_to_sample = 9216
        self.stop_sequences = [HUMAN_PROMPT]
        self.client = Client(claude_api)
        self.prompt = ''

    def reset(self):
        self.prompt = ''
        self.max_tokens_to_sample = 9216

    def change_model(self, model):
        valid_models = {'claude-v1', 'claude-v1.0', 'claude-v1.2',
                        'claude-v1.3', 'claude-instant-v1', 'claude-instant-v1.0'}
        if model in valid_models:
            self.model = model
            return True
        return False

    def change_temperature(self, temperature):
        try:
            temperature = float(temperature)
        except ValueError:
            return False
        if 0 <= temperature <= 1:
            self.temperature = temperature
            return True
        return False

    def change_cutoff(self, cutoff):
        try:
            cutoff = int(cutoff)
        except ValueError:
            return False
        if cutoff > 0:
            self.cutoff = cutoff
            return True
        return False

    def send_message_stream(self, message):
        self.prompt = f'{self.prompt}{HUMAN_PROMPT} {message}{AI_PROMPT}'
        self.max_tokens_to_sample -= count_tokens(self.prompt)
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
