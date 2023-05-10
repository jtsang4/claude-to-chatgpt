from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from claude_to_openai.adapter import ClaudeAdapter
import json
import os
from claude_to_openai.logger import logger

CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
PORT = os.getenv("PORT", 8000)

logger.debug(f"claude_base_url: {CLAUDE_BASE_URL}")

adapter = ClaudeAdapter(CLAUDE_BASE_URL)

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat(request: Request):
    openai_params = await request.json()
    if openai_params.get("stream", False):
        async def generate():
            async for response in adapter.chat(request):
                yield f"data: {json.dumps(response)}\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        openai_response = None
        async for response in adapter.chat(request):
            openai_response = response
        return JSONResponse(content=openai_response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, log_level=LOG_LEVEL)
