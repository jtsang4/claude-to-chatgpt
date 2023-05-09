from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import json
import os

claude_api_key = os.getenv("CLAUDE_API_KEY")
claude_base_url = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
adapter = ClaudeAdapter(claude_api_key, claude_base_url)

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat(request: Request):
    openai_params = await request.json()

    if openai_params.get("stream", False):
        def generate():
            for response in adapter.chat(openai_params):
                yield f"data: {json.dumps(response)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        openai_response = adapter.chat(openai_params)
        return JSONResponse(content=openai_response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info")
