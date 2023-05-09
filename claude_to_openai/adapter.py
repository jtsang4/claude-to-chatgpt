import requests
import time
import json
from claude_to_openai.util import num_tokens_from_string

role_map = {
    "system": "Human",
    "user": "Human",
    "assistant": "Assistant",
}

stop_reason_map = {
    "stop_sequence": "stop",
    "max_tokens": "length",
}

class ClaudeAdapter:
    def __init__(self, claude_api_key, claude_base_url="https://api.anthropic.com"):
        self.claude_api_key = claude_api_key
        self.claude_base_url = claude_base_url

    def convert_messages_to_prompt(self, messages):
        prompt = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            transformed_role = role_map[role]
            prompt += f"\n\n{transformed_role.capitalize()}: {content}"
        prompt += "\n\nAssistant:"
        return prompt

    def openai_to_claude_params(self, openai_params):
        model = openai_params["model"]
        messages = openai_params["messages"]

        prompt = self.convert_messages_to_prompt(messages)

        claude_params = {
            "model": "claude-v1.3",
            "prompt": prompt,
            "max_tokens_to_sample": openai_params["max_tokens"],
            "stop_sequences": openai_params["stop"],
        }

        return claude_params

    def claude_to_openai_response(self, claude_response):
        completion_tokens = num_tokens_from_string(claude_response["completion"])
        openai_response = {
            "id": None,
            "object": "chat.completion",
            "created": int(time.time()),
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": completion_tokens,
                "total_tokens": completion_tokens,
            },
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": claude_response["completion"],
                    },
                    "index": 0,
                    "finish_reason": stop_reason_map[claude_response["stop_reason"]],
                }
            ],
        }

        return openai_response

    def chat(self, openai_params):
        claude_params = self.openai_to_claude_params(openai_params)

        if claude_params["stream"]:
            response = requests.post(
                f"{self.claude_base_url}/v1/complete",
                headers={
                    "x-api-key": self.claude_api_key,
                    "content-type": "application/json",
                },
                json=claude_params,
                stream=True,
            )

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if decoded_line == "data: [DONE]":
                        break
                    else:
                        claude_response = json.loads(decoded_line[6:])
                        openai_response = self.claude_to_openai_response(claude_response)
                        yield openai_response
        else:
            response = requests.post(
                f"{self.claude_base_url}/v1/complete",
                headers={
                    "x-api-key": self.claude_api_key,
                    "content-type": "application/json",
                },
                json=claude_params,
            )

            if response.status_code == 200:
                claude_response = response.json()
                openai_response = self.claude_to_openai_response(claude_response)
                return openai_response
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")
