const version = '0.6.0';

addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});

const CLAUDE_API_KEY = ''; // Optional: default claude api key if you don't want to pass it in the request header
const CLAUDE_BASE_URL = 'https://api.anthropic.com/v1/messages'; // Changed to messages endpoint
const MAX_TOKENS = 4096;

function getAPIKey(headers) {
  const authorization = headers.authorization;
  if (authorization) {
    return authorization.split(' ')[1] || CLAUDE_API_KEY;
  }
  return CLAUDE_API_KEY;
}

function formatStreamResponseJson(claudeResponse) {
  switch (claudeResponse.type) {
    case 'message_start':
      return {
        id: claudeResponse.message.id,
        model: claudeResponse.message.model,
        inputTokens: claudeResponse.message.usage.input_tokens,
      };
    case 'content_block_start':
    case 'ping':
      return null;
    case 'content_block_delta':
      return {
        content: claudeResponse.delta.text,
      };
    case 'content_block_stop':
      return null;
    case 'message_delta':
      return {
        stopReason: claudeResponse.delta.stop_reason,
        outputTokens: claudeResponse.usage.output_tokens,
      };
    case 'message_stop':
      return null;
    default:
      return null;
  }
}

function claudeToChatGPTResponse(claudeResponse, metaInfo, stream = false) {
  const timestamp = Math.floor(Date.now() / 1000);
  const completionTokens = metaInfo.outputTokens || 0;
  const promptTokens = metaInfo.inputTokens || 0;
  if (metaInfo.stopReason && stream) {
    return {
      id: metaInfo.id,
      object: 'chat.completion.chunk',
      created: timestamp,
      model: metaInfo.model,
      choices: [
        {
          index: 0,
          delta: {},
          logprobs: null,
          finish_reason: 'stop',
        },
      ],
      usage: {
        prompt_tokens: promptTokens,
        completion_tokens: completionTokens,
        total_tokens: promptTokens + completionTokens,
      },
    };
  }
  const content = claudeResponse.content;
  const result = {
    id: metaInfo.id || 'unknown',
    created: timestamp,
    model: metaInfo.model,
    usage: {
      prompt_tokens: promptTokens,
      completion_tokens: completionTokens,
      total_tokens: promptTokens + completionTokens,
    },
    choices: [
      {
        index: 0,
        finish_reason: metaInfo.stopReason === 'end_turn' ? 'stop' : null,
      },
    ],
  };
  const message = {
    role: 'assistant',
    content: content || '',
  };
  if (!stream) {
    result.object = 'chat.completion';
    result.choices[0].message = message;
  } else {
    result.object = 'chat.completion.chunk';
    result.choices[0].delta = message;
  }
  return result;
}

async function streamJsonResponseBodies(response, writable, model) {
  const reader = response.body.getReader();
  const writer = writable.getWriter();

  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  let buffer = '';
  const metaInfo = {
    model,
  };
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      writer.write(encoder.encode('data: [DONE]'));
      break;
    }
    const currentText = decoder.decode(value, { stream: true }); // stream: true is important here,fix the bug of incomplete line
    buffer += currentText;
    console.log('🚀 ~ streamJsonResponseBodies ~ buffer:', buffer);
    const regex = /event:\s*.*?\s*\ndata:\s*(.*?)(?=\n\n|\s*$)/gs;

    let match;
    while ((match = regex.exec(buffer)) !== null) {
      try {
        const decodedLine = JSON.parse(match[1].trim());
        const formatedChunk = formatStreamResponseJson(decodedLine);
        if (formatedChunk === null) {
          continue;
        }
        metaInfo.id = formatedChunk.id ?? metaInfo.id;
        metaInfo.model = formatedChunk.model ?? metaInfo.model;
        metaInfo.inputTokens =
          formatedChunk.inputTokens ?? metaInfo.inputTokens;
        metaInfo.outputTokens =
          formatedChunk.outputTokens ?? metaInfo.outputTokens;
        metaInfo.stopReason = formatedChunk.stopReason ?? metaInfo.stopReason;
        const transformedLine = claudeToChatGPTResponse(
          formatedChunk,
          metaInfo,
          true
        );
        writer.write(
          encoder.encode(`data: ${JSON.stringify(transformedLine)}\n\n`)
        );
      } catch (e) {}
      // 从buffer中移除已处理的部分
      buffer = buffer.slice(match.index + match[0].length);
    }
  }
  await writer.close();
}

async function handleRequest(request) {
  if (request.method === 'GET') {
    const path = new URL(request.url).pathname;
    if (path === '/v1/models') {
      return new Response(
        JSON.stringify({
          object: 'list',
          data: models_list,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
    return new Response('Not Found', { status: 404 });
  } else if (request.method === 'OPTIONS') {
    return handleOPTIONS();
  } else if (request.method === 'POST') {
    const headers = Object.fromEntries(request.headers);
    const apiKey = getAPIKey(headers);
    if (!apiKey) {
      return new Response('Not Allowed', {
        status: 403,
      });
    }

    const requestBody = await request.json();
    const { model, messages, temperature, stop, stream } = requestBody;
    const claudeModel = model;

    // Convert OpenAI API request to Claude API request
    const systemMessage = messages.find((message) => message.role === 'system');
    const claudeRequestBody = {
      model: claudeModel,
      messages: messages.filter((message) => message.role !== 'system'),
      temperature,
      max_tokens: MAX_TOKENS,
      stop_sequences: stop,
      system: systemMessage?.content,
      stream,
    };

    const claudeResponse = await fetch(CLAUDE_BASE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify(claudeRequestBody),
    });

    if (!stream) {
      const claudeResponseBody = await claudeResponse.json();
      const formatedResult = {
        id: claudeResponseBody.id,
        model: claudeResponseBody.model,
        inputTokens: claudeResponseBody.usage.input_tokens,
        outputTokens: claudeResponseBody.usage.output_tokens,
        stopReason: claudeResponseBody.stop_reason,
      };
      const openAIResponseBody = claudeToChatGPTResponse(
        { content: claudeResponseBody.content[0].text },
        formatedResult
      );
      if (openAIResponseBody === null) {
        return new Response('Error processing Claude response', {
          status: 500,
        });
      }
      return new Response(JSON.stringify(openAIResponseBody), {
        status: claudeResponse.status,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': '*',
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Credentials': 'true',
        },
      });
    } else {
      // Implement streaming logic here
      const { readable, writable } = new TransformStream();
      streamJsonResponseBodies(claudeResponse, writable);
      return new Response(readable, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': '*',
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Credentials': 'true',
        },
      });
    }
  } else {
    return new Response('Method not allowed', { status: 405 });
  }
}

function handleOPTIONS() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': '*',
      'Access-Control-Allow-Headers': '*',
      'Access-Control-Allow-Credentials': 'true',
    },
  });
}

const models_list = [
  {
    id: 'gpt-3.5-turbo',
    object: 'model',
    created: 1677610602,
    owned_by: 'openai',
    permission: [
      {
        id: 'modelperm-YO9wdQnaovI4GD1HLV59M0AV',
        object: 'model_permission',
        created: 1683753011,
        allow_create_engine: false,
        allow_sampling: true,
        allow_logprobs: true,
        allow_search_indices: false,
        allow_view: true,
        allow_fine_tuning: false,
        organization: '*',
        group: null,
        is_blocking: false,
      },
    ],
    root: 'gpt-3.5-turbo',
    parent: null,
  },
  {
    id: 'gpt-3.5-turbo-0613',
    object: 'model',
    created: 1677649963,
    owned_by: 'openai',
    permission: [
      {
        id: 'modelperm-tsdKKNwiNtHfnKWWTkKChjoo',
        object: 'model_permission',
        created: 1683753015,
        allow_create_engine: false,
        allow_sampling: true,
        allow_logprobs: true,
        allow_search_indices: false,
        allow_view: true,
        allow_fine_tuning: false,
        organization: '*',
        group: null,
        is_blocking: false,
      },
    ],
    root: 'gpt-3.5-turbo-0613',
    parent: null,
  },
  {
    id: 'gpt-4',
    object: 'model',
    created: 1678604602,
    owned_by: 'openai',
    permission: [
      {
        id: 'modelperm-nqKDpzYoZMlqbIltZojY48n9',
        object: 'model_permission',
        created: 1683768705,
        allow_create_engine: false,
        allow_sampling: false,
        allow_logprobs: false,
        allow_search_indices: false,
        allow_view: false,
        allow_fine_tuning: false,
        organization: '*',
        group: null,
        is_blocking: false,
      },
    ],
    root: 'gpt-4',
    parent: null,
  },
  {
    id: 'gpt-4-0613',
    object: 'model',
    created: 1678604601,
    owned_by: 'openai',
    permission: [
      {
        id: 'modelperm-PGbNkIIZZLRipow1uFL0LCvV',
        object: 'model_permission',
        created: 1683768678,
        allow_create_engine: false,
        allow_sampling: false,
        allow_logprobs: false,
        allow_search_indices: false,
        allow_view: false,
        allow_fine_tuning: false,
        organization: '*',
        group: null,
        is_blocking: false,
      },
    ],
    root: 'gpt-4-0613',
    parent: null,
  },
];
