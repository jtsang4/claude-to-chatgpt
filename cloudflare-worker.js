addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});

const CLAUDE_API_KEY = ''; // Optional: default claude api key if you don't want to pass it in the request header
const CLAUDE_BASE_URL = 'https://api.anthropic.com';

const role_map = {
  system: 'Human',
  user: 'Human',
  assistant: 'Assistant',
};

const stop_reason_map = {
  stop_sequence: 'stop',
  max_tokens: 'length',
};

function convertMessagesToPrompt(messages) {
  let prompt = '';
  for (const message of messages) {
    const role = message['role'];
    const content = message['content'];
    const transformed_role = role_map[role] || 'Human';
    prompt += `\n\n${transformed_role}: ${content}`;
  }
  prompt += '\n\nAssistant: ';
  return prompt;
}

function getAPIKey(headers) {
  const authorization = headers.authorization;
  if (authorization) {
    return authorization.split(' ')[1] || CLAUDE_API_KEY;
  }
  return CLAUDE_API_KEY;
}

function claudeToChatGPTResponse(claudeResponse) {
  const completion = claudeResponse['completion'];
  const timestamp = Math.floor(Date.now() / 1000);
  const completionTokens = completion.split(' ').length;
  return {
    id: `chatcmpl-${timestamp}`,
    object: 'chat.completion',
    created: timestamp,
    usage: {
      prompt_tokens: 0,
      completion_tokens: completionTokens,
      total_tokens: completionTokens,
    },
    choices: [
      {
        message: {
          role: 'assistant',
          content: completion,
        },
        index: 0,
        finish_reason: claudeResponse['stop_reason']
          ? stop_reason_map[claudeResponse['stop_reason']]
          : null,
      },
    ],
  };
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
    const claudeModel = model_map[model] || 'claude-v1.3-100k';

    // OpenAI API 转换为 Claude API
    const prompt = convertMessagesToPrompt(messages);
    let maxTokensToSample = 100000;
    if (model !== 'claude-v1.3-100k') {
      maxTokensToSample = 9016;
    }
    const claudeRequestBody = {
      prompt,
      model: claudeModel,
      temperature,
      max_tokens_to_sample: maxTokensToSample,
      stop_sequences: stop,
      stream,
    };

    // 调用 Claude API
    const claudeResponse = await fetch(`${CLAUDE_BASE_URL}/v1/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
      },
      body: JSON.stringify(claudeRequestBody),
    });

    const claudeResponseBody = await claudeResponse.json();

    const openAIResponseBody = claudeToChatGPTResponse(claudeResponseBody);

    return new Response(JSON.stringify(openAIResponseBody), {
      status: claudeResponse.status,
      headers: { 'Content-Type': 'application/json' },
    });
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
    id: 'gpt-3.5-turbo-0301',
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
    root: 'gpt-3.5-turbo-0301',
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
    id: 'gpt-4-0314',
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
    root: 'gpt-4-0314',
    parent: null,
  },
];

const model_map = {
  'gpt-3.5-turbo': 'claude-v1.3-100k',
  'gpt-3.5-turbo-0301': 'claude-v1.3',
  'gpt-4': 'claude-v1.3-100k',
  'gpt-4-0314': 'claude-v1.3-100k',
};
