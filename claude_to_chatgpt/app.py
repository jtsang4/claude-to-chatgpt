from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from claude_to_chatgpt.adapter import ClaudeAdapter
import json
import os
from claude_to_chatgpt.logger import logger
from claude_to_chatgpt.models import models_list

CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
PORT = os.getenv("PORT", 8000)

logger.debug(f"claude_base_url: {CLAUDE_BASE_URL}")

adapter = ClaudeAdapter(CLAUDE_BASE_URL)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods, including OPTIONS
    allow_headers=["*"],
)


@app.get("/")
async def hello():
    return "hello claude server"


@app.api_route(
    "/v1/chat/completions",
    methods=["POST", "OPTIONS"],
)
async def chat(request: Request):
    openai_params = await request.json()
    if openai_params.get("stream", False):

        async def generate():
            async for response in adapter.chat(request):
                if response == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break
                yield f"data: {json.dumps(response)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        response = adapter.chat(request)
        openai_response = await response.__anext__()
        return JSONResponse(content=openai_response)


@app.route("/v1/models", methods=["GET"])
async def models(request: Request):
    # return a dict with key "object" and "data", "object" value is "list", "data" values is models list
    return JSONResponse(content={"object": "list", "data": models_list})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(PORT), log_level=LOG_LEVEL)
