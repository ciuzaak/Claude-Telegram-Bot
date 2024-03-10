from anthropic import AI_PROMPT, HUMAN_PROMPT, AsyncAnthropic

from config import claude_api


class Claude:
    def __init__(self):
        self.model = "claude-3-opus-20240229"
        self.temperature = 0.7
        self.cutoff = 50
        self.client = AsyncAnthropic(api_key=claude_api)
        self.prompt = ""

    def reset(self):
        self.prompt = ""

    def revert(self):
        self.prompt = self.prompt[: self.prompt.rfind(HUMAN_PROMPT)]

    def change_model(self, model):
        valid_models = {"claude-3-opus-20240229", "claude-3-sonett-20240229"}
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

    async def send_message_stream(self, message) -> None:
        self.prompt = f"{self.prompt}{HUMAN_PROMPT} {message}{AI_PROMPT}"
        answer = ""
        async with self.client.messages.stream(
          max_tokens=1024,
          model=self.model,
          messages=[
              {
                  "role": "user",
                  "content": self.prompt,
              }
            ],
        ) as stream:
          async for text in stream.text_stream:
            answer = f"{answer}{text}"
            yield answer
        self.prompt = f"{self.prompt}{answer}"
        message = await stream.get_final_message()
        print(message.model_dump_json(indent=2))
