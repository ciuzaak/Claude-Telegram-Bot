from anthropic import AI_PROMPT, HUMAN_PROMPT, AsyncAnthropic

from config import claude_api


class Claude:
    def __init__(self):
        self.model = "claude-1.3-100k"
        self.temperature = 0.7
        self.cutoff = 50
        self.client = AsyncAnthropic(api_key=claude_api)
        self.prompt = ""

    def reset(self):
        self.prompt = ""

    def revert(self):
        self.prompt = self.prompt[: self.prompt.rfind(HUMAN_PROMPT)]

    def change_model(self, model):
        valid_models = {
            "claude-1",
            "claude-1-100k",
            "claude-instant-1",
            "claude-instant-1-100k",
            "claude-1.3",
            "claude-1.3-100k",
            "claude-1.2",
            "claude-1.0",
            "claude-instant-1.1",
            "claude-instant-1.1-100k",
            "claude-instant-1.0",
        }
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

    async def send_message_stream(self, message):
        self.prompt = f"{self.prompt}{HUMAN_PROMPT} {message}{AI_PROMPT}"
        response = await self.client.completions.create(
            prompt=self.prompt,
            stop_sequences=[HUMAN_PROMPT],
            max_tokens_to_sample=9216,
            model=self.model,
            temperature=self.temperature,
            stream=True,
        )
        answer = ""
        async for data in response:
            answer = f"{answer}{data.completion}"
            yield answer
        self.prompt = f"{self.prompt}{answer}"
