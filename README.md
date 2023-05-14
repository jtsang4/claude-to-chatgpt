<h4 align="right">
  <strong>English</strong> | <a href="https://github.com/jtsang4/claude-to-chatgpt/blob/main/README_CN.md">简体中文</a>
</h4>

<div>
  <h1 align="center">Claude to ChatGPT</h1>
  <p align="center">
    <a href="https://github.com/jtsang4/claude-to-chatgpt/releases" target="_blank">
        <img src="https://github.com/jtsang4/claude-to-chatgpt/actions/workflows/docker.yaml/badge.svg" alt="release">
    </a>
    <a href="https://github.com/jtsang4/claude-to-chatgpt/releases">
        <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/jtsang4/claude-to-chatgpt?style=flat">
    </a>
    <a href="https://github.com/jtsang4/claude-to-chatgpt/releases">
        <img alt="GitHub Repo Badge" src="https://img.shields.io/badge/anthropic-claude-orange?style=flat">
    </a>
    <a href="https://github.com/jtsang4/claude-to-chatgpt/releases">
        <img alt="GitHub Repo Language" src="https://img.shields.io/badge/langurage-js/py-brightgreen?style=flat&color=blue">
    </a>
  </p>
</div>

This project converts the API of Anthropic's Claude model to the OpenAI Chat API format.

* ✨ Call Claude API like OpenAI ChatGPT API
* 💦 Support streaming response
* 🐻 Support `claude-v1.3`, `claude-v1.3-100k` models
* 🌩️ Deploy by Cloudflare Workers or Docker

## Getting Started

You can run this project using Cloudflare Workers or Docker:

### Deployment

#### Using Cloudflare Workers

By using Cloudflare Workers, you don't need a server to deploy this project.

1. Create a Cloudflare Worker
2. Paste the code in [`cloudflare-worker.js`](https://github.com/jtsang4/claude-to-chatgpt/blob/main/cloudflare-worker.js) to Cloudflare Worker "Quick Edit" Editor
3. Save and deploy
4. (Optional) Set custom domain for your Cloudflare Worker

The Cloudfalre Workers support 100k requests a day, If you need to call more than that, you can use Docker to deploy as below.

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


#### GUI

Here are some recommended GUI software that supports this project:

* [Bin-Huang/chatbox](https://github.com/Bin-Huang/chatbox)
* [Yidadaa/ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)

#### CLI

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

The OpenAI Chat API has a similar `/v1/chat/completions` endpoint which takes:

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