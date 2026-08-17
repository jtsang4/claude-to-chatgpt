import json
import os
import time

import httpx
from fastapi import Request

from claude_to_chatgpt.models import openai_model_aliases


stop_reason_map = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "max_tokens": "length",
    "tool_use": "tool_calls",
}


class ClaudeAdapter:
    def __init__(
        self,
        claude_base_url="https://api.anthropic.com",
        client_factory=None,
    ):
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.claude_base_url = claude_base_url.rstrip("/")
        self.default_model = os.getenv(
            "CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-20250514"
        )
        self.client_factory = client_factory or (
            lambda: httpx.AsyncClient(timeout=120.0)
        )

    def get_api_key(self, headers):
        auth_header = headers.get("authorization")
        if auth_header:
            scheme, separator, credentials = auth_header.partition(" ")
            if (
                not separator
                or scheme.lower() != "bearer"
                or not credentials.strip()
            ):
                raise ValueError("Authorization must use a Bearer token")
            return credentials.strip()
        if self.claude_api_key:
            return self.claude_api_key
        raise ValueError("No Anthropic API key was provided")

    def resolve_model(self, requested_model):
        if requested_model in openai_model_aliases:
            return self.default_model
        return requested_model or self.default_model

    def openai_to_claude_params(self, openai_params):
        system_messages = []
        messages = []
        for message in openai_params["messages"]:
            if message["role"] == "system":
                content = message["content"]
                if not isinstance(content, str):
                    raise ValueError("System message content must be text")
                system_messages.append(content)
                continue
            if message["role"] not in {"user", "assistant"}:
                raise ValueError(f"Unsupported message role: {message['role']}")
            messages.append(
                {"role": message["role"], "content": message["content"]}
            )

        if not messages:
            raise ValueError("At least one user or assistant message is required")

        claude_params = {
            "model": self.resolve_model(openai_params.get("model")),
            "messages": messages,
            "max_tokens": openai_params.get("max_tokens", 1024),
        }

        if system_messages:
            claude_params["system"] = "\n\n".join(system_messages)
        if openai_params.get("stop"):
            stop = openai_params["stop"]
            claude_params["stop_sequences"] = (
                stop if isinstance(stop, list) else [stop]
            )
        if openai_params.get("temperature") is not None:
            claude_params["temperature"] = openai_params["temperature"]
        if openai_params.get("top_p") is not None:
            claude_params["top_p"] = openai_params["top_p"]
        if openai_params.get("stream"):
            claude_params["stream"] = True

        return claude_params

    @staticmethod
    def _text_content(content):
        return "".join(
            block.get("text", "")
            for block in content
            if block.get("type") == "text"
        )

    @staticmethod
    def _usage(usage):
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def claude_to_chatgpt_response(self, claude_response, requested_model):
        return {
            "id": claude_response["id"],
            "object": "chat.completion",
            "created": int(time.time()),
            "model": requested_model,
            "usage": self._usage(claude_response.get("usage", {})),
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": self._text_content(
                            claude_response.get("content", [])
                        ),
                    },
                    "index": 0,
                    "finish_reason": stop_reason_map.get(
                        claude_response.get("stop_reason")
                    ),
                }
            ],
        }

    @staticmethod
    def _stream_chunk(
        stream_state,
        requested_model,
        delta=None,
        finish_reason=None,
        usage=None,
    ):
        chunk = {
            "id": stream_state["id"],
            "object": "chat.completion.chunk",
            "created": stream_state["created"],
            "model": requested_model,
            "choices": [
                {
                    "delta": delta or {},
                    "index": 0,
                    "finish_reason": finish_reason,
                }
            ],
        }
        if usage is not None:
            chunk["usage"] = usage
        return chunk

    def convert_stream_event(self, event, stream_state, requested_model):
        event_type = event.get("type")

        if event_type == "message_start":
            message = event["message"]
            stream_state.update(
                {
                    "id": message["id"],
                    "created": int(time.time()),
                    "input_tokens": message.get("usage", {}).get(
                        "input_tokens", 0
                    ),
                    "output_tokens": 0,
                }
            )
            return self._stream_chunk(
                stream_state,
                requested_model,
                delta={"role": "assistant", "content": ""},
            )

        if event_type == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return self._stream_chunk(
                    stream_state,
                    requested_model,
                    delta={"content": delta.get("text", "")},
                )
            return None

        if event_type == "message_delta":
            stream_state["output_tokens"] = event.get("usage", {}).get(
                "output_tokens", stream_state.get("output_tokens", 0)
            )
            usage = self._usage(
                {
                    "input_tokens": stream_state.get("input_tokens", 0),
                    "output_tokens": stream_state.get("output_tokens", 0),
                }
            )
            return self._stream_chunk(
                stream_state,
                requested_model,
                finish_reason=stop_reason_map.get(
                    event.get("delta", {}).get("stop_reason")
                ),
                usage=usage,
            )

        if event_type == "error":
            error = event.get("error", {})
            raise RuntimeError(
                f"Anthropic stream error: {error.get('type', 'unknown')}: "
                f"{error.get('message', '')}"
            )

        return None

    @staticmethod
    def _decode_sse_data(line):
        if not line.startswith("data:"):
            return None
        data = line[len("data:") :].strip()
        if not data:
            return None
        return json.loads(data)

    async def chat(self, request: Request):
        openai_params = await request.json()
        requested_model = openai_params.get("model", "gpt-3.5-turbo")
        claude_params = self.openai_to_claude_params(openai_params)
        api_key = self.get_api_key(request.headers)
        headers = {
            "x-api-key": api_key,
            "accept": "application/json",
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        async with self.client_factory() as client:
            if not claude_params.get("stream", False):
                response = await client.post(
                    f"{self.claude_base_url}/v1/messages",
                    headers=headers,
                    json=claude_params,
                )
                response.raise_for_status()
                yield self.claude_to_chatgpt_response(
                    response.json(), requested_model
                )
                return

            stream_state = {}
            async with client.stream(
                "POST",
                f"{self.claude_base_url}/v1/messages",
                headers=headers,
                json=claude_params,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    event = self._decode_sse_data(line)
                    if event is None:
                        continue
                    chunk = self.convert_stream_event(
                        event, stream_state, requested_model
                    )
                    if chunk is not None:
                        yield chunk
                    if event.get("type") == "message_stop":
                        yield "[DONE]"
                        return
