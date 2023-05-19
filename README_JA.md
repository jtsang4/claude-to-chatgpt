<h4 align="right">
  <a href="https://github.com/jtsang4/claude-to-chatgpt">English</a> | <a href="https://github.com/jtsang4/claude-to-chatgpt/blob/main/README_CN.md">简体中文</a> | <strong>日本語</strong>
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

本プロジェクトでは、Anthropic の Claude モデルの API を OpenAI Chat API 形式に変換しています。

- ✨ OpenAI ChatGPT API のように Claude API を呼び出す
- 💦 ストリーミングレス対応
- 🐻 `claude-v1.3`, `claude-v1.3-100k` のモデルをサポートする
- 🌩️ Cloudflare Workers や Docker でデプロイする

## はじめに

このプロジェクトは、Cloudflare Workers または Docker を使用して実行することができます:

### デプロイ

#### Cloudflare Workers の利用について

Cloudflare Workers を利用することで、このプロジェクトを展開するためのサーバーが不要になります。

1. Cloudflare Worker を作成する
2. [`Cloudflare-worker.js`](https://github.com/jtsang4/claude-to-chatgpt/blob/main/cloudflare-worker.js)のコードを Cloudflare Worker の "Quick Edit" エディタに貼り付けます。
3. 保存してデプロイする
4. オプションとして、Cloudflare Worker にカスタムドメインを設定します

Cloudfalre Workers は 1 日 10 万件のリクエストをサポートしていますが、それ以上呼ぶ必要がある場合は、以下のように Docker を使ってデプロイします。

#### Docker の使用

```bash
docker run -p 8000:8000 wtzeng/claude-to-chatgpt:latest
```

#### Docker Compose の使用

```bash
docker-compose up
```

その後、http://localhost:8000、API が利用できるようになります。API エンドポイント: `/v1/chat/completions`

### 使用方法

モデルパラメータを `gpt-3.5-turbo` または `gpt-3.5-turbo-0301` と入力すると `claude-v1.3` に置換されます。

#### GUI

このプロジェクトをサポートする、おすすめの GUI ソフトをご紹介します:

- [Bin-Huang/chatbox](https://github.com/Bin-Huang/chatbox)
- [Yidadaa/ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)

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

## コンバージョンの詳細

Claude Completion API にはエンドポイント `/v1/complete` があり、以下の JSON リクエストを受け取ります:

```json
{
  "prompt": "\n\nHuman: Hello, AI.\n\nAssistant: ",
  "model": "claude-v1.3",
  "max_tokens_to_sample": 100,
  "temperature": 1,
  "stream": true
}
```

そして、選択肢と完了を含む JSON を返します。

OpenAI Chat API には同様の `/v1/chat/completions` エンドポイントがあり、これは次のように受け取ります:

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

そして、応答文字列を持つ JSON を返します。

このプロジェクトはこれら 2 つの API 間を変換し、Claude モデルから完了を取得し、OpenAI Chat のレスポンスとしてフォーマットします。

## ライセンス

このプロジェクトは MIT ライセンスでライセンスされています - 詳しくは、LICENSE ファイルをご覧ください。
