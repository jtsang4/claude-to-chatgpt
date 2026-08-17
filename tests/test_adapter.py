import json

import httpx
import pytest
from starlette.requests import Request

from claude_to_chatgpt.adapter import ClaudeAdapter


def make_request(payload, api_key="test-key"):
    body = json.dumps(payload).encode()
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/chat/completions",
            "headers": [
                (b"authorization", f"Bearer {api_key}".encode()),
                (b"content-type", b"application/json"),
            ],
        },
        receive,
    )


def test_openai_request_converts_to_messages_api():
    adapter = ClaudeAdapter()

    result = adapter.openai_to_claude_params(
        {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
                {"role": "user", "content": "Continue"},
            ],
            "max_tokens": 200,
            "temperature": 0,
            "top_p": 0.9,
            "stop": "END",
            "stream": True,
        }
    )

    assert result == {
        "model": "claude-sonnet-4-20250514",
        "system": "Be concise.",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Continue"},
        ],
        "max_tokens": 200,
        "temperature": 0,
        "top_p": 0.9,
        "stop_sequences": ["END"],
        "stream": True,
    }


def test_native_claude_model_passes_through():
    adapter = ClaudeAdapter()
    result = adapter.openai_to_claude_params(
        {
            "model": "claude-opus-4-1",
            "messages": [{"role": "user", "content": "Hello"}],
        }
    )

    assert result["model"] == "claude-opus-4-1"
    assert result["max_tokens"] == 1024


def test_invalid_message_role_fails_closed():
    adapter = ClaudeAdapter()

    with pytest.raises(ValueError, match="Unsupported message role"):
        adapter.openai_to_claude_params(
            {
                "model": "gpt-4",
                "messages": [{"role": "tool", "content": "result"}],
            }
        )


def test_api_key_requires_bearer_scheme(monkeypatch):
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    adapter = ClaudeAdapter()

    assert (
        adapter.get_api_key({"authorization": "Bearer test-key"})
        == "test-key"
    )
    with pytest.raises(ValueError, match="Bearer"):
        adapter.get_api_key({"authorization": "Basic test-key"})
    with pytest.raises(ValueError, match="No Anthropic API key"):
        adapter.get_api_key({})


def test_messages_response_converts_to_openai_shape():
    adapter = ClaudeAdapter()
    response = adapter.claude_to_chatgpt_response(
        {
            "id": "msg_123",
            "model": "claude-sonnet-4-20250514",
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": " world"},
            ],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 8, "output_tokens": 2},
        },
        "gpt-4",
    )

    assert response["id"] == "msg_123"
    assert response["model"] == "gpt-4"
    assert response["choices"][0]["message"]["content"] == "Hello world"
    assert response["choices"][0]["finish_reason"] == "stop"
    assert response["usage"] == {
        "prompt_tokens": 8,
        "completion_tokens": 2,
        "total_tokens": 10,
    }


def test_stream_events_convert_to_openai_chunks():
    adapter = ClaudeAdapter()
    state = {}

    start = adapter.convert_stream_event(
        {
            "type": "message_start",
            "message": {
                "id": "msg_stream",
                "usage": {"input_tokens": 6, "output_tokens": 1},
            },
        },
        state,
        "gpt-4",
    )
    text = adapter.convert_stream_event(
        {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Hello"},
        },
        state,
        "gpt-4",
    )
    finish = adapter.convert_stream_event(
        {
            "type": "message_delta",
            "delta": {"stop_reason": "max_tokens"},
            "usage": {"output_tokens": 4},
        },
        state,
        "gpt-4",
    )

    assert start["choices"][0]["delta"] == {
        "role": "assistant",
        "content": "",
    }
    assert text["choices"][0]["delta"] == {"content": "Hello"}
    assert finish["choices"][0]["finish_reason"] == "length"
    assert finish["usage"]["total_tokens"] == 10


def test_stream_ignores_unknown_events_and_raises_api_errors():
    adapter = ClaudeAdapter()
    state = {"id": "msg", "created": 1}

    assert (
        adapter.convert_stream_event(
            {"type": "ping"}, state, "gpt-4"
        )
        is None
    )
    with pytest.raises(RuntimeError, match="overloaded_error"):
        adapter.convert_stream_event(
            {
                "type": "error",
                "error": {
                    "type": "overloaded_error",
                    "message": "Try again",
                },
            },
            state,
            "gpt-4",
        )


def test_sse_parser_only_decodes_data_lines():
    assert ClaudeAdapter._decode_sse_data("event: message_start") is None
    assert ClaudeAdapter._decode_sse_data("data:") is None
    assert ClaudeAdapter._decode_sse_data(
        'data: {"type":"message_stop"}'
    ) == {"type": "message_stop"}
    with pytest.raises(json.JSONDecodeError):
        ClaudeAdapter._decode_sse_data("data: not-json")


@pytest.mark.asyncio
async def test_chat_posts_to_messages_endpoint_without_network():
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["headers"] = request.headers
        captured["json"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "msg_mock",
                "model": "claude-sonnet-4-20250514",
                "content": [{"type": "text", "text": "Mock reply"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 3, "output_tokens": 2},
            },
        )

    transport = httpx.MockTransport(handler)
    adapter = ClaudeAdapter(
        client_factory=lambda: httpx.AsyncClient(transport=transport)
    )
    request = make_request(
        {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }
    )

    output = [item async for item in adapter.chat(request)]

    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"]["x-api-key"] == "test-key"
    assert captured["json"]["messages"] == [
        {"role": "user", "content": "Hello"}
    ]
    assert output[0]["choices"][0]["message"]["content"] == "Mock reply"


@pytest.mark.asyncio
async def test_chat_converts_complete_messages_sse_sequence():
    events = [
        {
            "type": "message_start",
            "message": {
                "id": "msg_stream",
                "usage": {"input_tokens": 5, "output_tokens": 1},
            },
        },
        {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Hello"},
        },
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn"},
            "usage": {"output_tokens": 2},
        },
        {"type": "message_stop"},
    ]
    body = "".join(
        f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
        for event in events
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=body.encode(),
        )
    )
    adapter = ClaudeAdapter(
        client_factory=lambda: httpx.AsyncClient(transport=transport)
    )
    request = make_request(
        {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        }
    )

    output = [item async for item in adapter.chat(request)]

    assert output[0]["choices"][0]["delta"]["role"] == "assistant"
    assert output[1]["choices"][0]["delta"]["content"] == "Hello"
    assert output[2]["choices"][0]["finish_reason"] == "stop"
    assert output[2]["usage"]["total_tokens"] == 7
    assert output[3] == "[DONE]"
