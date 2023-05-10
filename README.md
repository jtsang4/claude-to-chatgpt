# Claude to OpenAI

This project converts the API of Anthropic's Claude model to the OpenAI Chat API format.

* ✨ Call Claude API like OpenAI ChatGPT API
* 💦 Support streaming response
* 🐻 Only support `claude-v1.3` model currently

## Getting Started

You can run this project using Docker or Docker Compose:

### Using Docker

```bash
docker build . -t claude-to-chatgpt
docker run -p 8000:8000 claude-to-chatgpt
```

#### Using Docker Compose (TODO)

```bash
docker-compose up
```


The API will then be available at http://localhost:8000. API endpoint: `/v1/chat/completions`

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