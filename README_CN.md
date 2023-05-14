<h4 align="right">
  <strong>简体中文</strong> | <a href="https://github.com/jtsang4/claude-to-chatgpt">English</a>
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

此项目将 Anthropic 的 Claude 模型的 API 转换为 OpenAI Chat API 格式。

* ✨ 以 OpenAI ChatGPT API 的方式调用 Claude API
* 💦 支持流式响应，实现打印机效果
* 🐻 支持 `claude-v1.3`，`claude-v1.3-100k` 模型
* 🌩️ 通过 Cloudflare Workers 或 Docker 部署

## 开始使用

您可以使用 Cloudflare Workers 或 Docker 进行部署：

### 部署

#### 使用 Cloudflare Workers

通过使用 Cloudflare Workers，您无需服务器即可部署此项目。

1. 创建一个 Cloudflare Worker
2. 将 [`cloudflare-worker.js`](https://github.com/jtsang4/claude-to-chatgpt/blob/main/cloudflare-worker.js) 中的代码粘贴到 Cloudflare Worker 的“快速编辑”编辑器中
3. 保存并部署
4. （可选）为 Cloudflare Worker 设置自定义域名

Cloudfalre Workers 支持每天 100k 请求，如果需要发起更多调用，请参照下面的方式使用 Docker 进行部署。

#### 使用 Docker

```bash
docker run -p 8000:8000 wtzeng/claude-to-chatgpt:latest
```

#### 使用 Docker Compose

```bash
docker-compose up
```

然后，API 将在 `http://localhost:8000` 上可用。API 路径：`/v1/chat/completions`。

### 使用方法

当您将模型参数 `model` 为 `gpt-3.5-turbo-0301` 时，它将替换为 `claude-v1.3`。否则，将使用 `claude-v1.3-100k`。


#### 图形界面软件

以下是一些支持使用本项目的推荐 GUI 软件：

* [Bin-Huang/chatbox](https://github.com/Bin-Huang/chatbox)
* [Yidadaa/ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)

#### 命令行调用

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CLAUDE_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 转换细节

Claude Completion API endpoint 为 `/v1/complete`，它接受以下请求格式并返回 Completion 接口的内容。：

```json
{
  "prompt": "\n\nHuman: Hello, AI.\n\nAssistant: ",
  "model": "claude-v1.3",
  "max_tokens_to_sample": 100,
  "temperature": 1,
  "stream": true
}
```

OpenAI Chat API 有一个相似的 `/v1/chat/completions` API，它接受以下请求格式：

```json
{
  "model": "gpt-3.5-turbo",
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

此项目在这两个 API 之间进行转换，从 Claude 模型获取返回结果并将它们格式化为 OpenAI ChatAPI 的响应。

## 许可证

此项目为 MIT 许可证授权，有关详细信息，请参阅 LICENSE 文件。
