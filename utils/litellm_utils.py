import litellm
from config import claude_api

class liteLLM:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.prompt = ""

    def reset(self):
        self.prompt = ""

    def change_model(self, model):
        # see litellm supported models here: https://litellm.readthedocs.io/en/latest/supported/
        if model in litellm.model_list:
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
        messages = [
                { "role": "system", "content": self.prompt },
                { "role": "user", "content": message }
            ]
        
        # call models using gpt3.5 format
        # use Azure, OpenAI, Anthropic, Cohere, Replicate, Bard LLMs
        response = await litellm.completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            stream=True,
        )
        answer = ""

        async for chunk in response:
            chunk_message = chunk['choices'][0]['delta']
            yield answer

