# Claude to ChatGPT

This project converts the API of Anthropic's Claude model to the OpenAI Chat API format.

* ✨ Call Claude API like OpenAI ChatGPT API
* 💦 Support streaming response
* 🐻 Support `claude-v1.3`, `claude-v1.3-100k` models

## Getting Started

You can run this project using Docker or Docker Compose:

### Deployment

#### Using Docker

```bash
docker run -p 8000:8000 wtzeng/claude-to-chatgpt:latest
```

#### Using Docker Compose

```bash
docker-compose up
```


The API will then be available at http://localhost:8000. API endpoint: `/v1/chat/completions`

### Usage

When you input the model parameter as `gpt-3.5-turbo-0301`, it will be substituted with `claude-v1.3`. otherwise, `claude-v1.3-100k` will be utilized.

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CLAUDE_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Conversion Details

The Claude Completion API has an endpoint `/v1/complete` which takes the following JSON request:

```json
{
  "prompt": "\n\nHuman: Hello, AI.\n\nAssistant: ",
  "model": "claude-v1.3",
  "max_tokens_to_sample": 100,
  "temperature": 1,
  "stream": true
}
```


And returns JSON with choices and completions.

The OpenAI Chat API has a simpler `/v1/chat/completions` endpoint which takes:

```json
{
  "model": "gpt-3.5-turbo", // will be ignored if you pass this param
  "messages": [
    {
      "role": "user",
      "content": "Hello, AI."
    }
  ],
  "max_tokens": 100,
  "temperature": 1,
  "stream": true
}
```


And returns JSON with a response string.

This project converts between these two APIs, get completions from the Claude model and formatting them as OpenAI Chat responses.

## License

This project is licensed under the MIT License - see the LICENSE file for details.