import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import { mapChatResponse } from './chatAdapter.js';

const here = dirname(fileURLToPath(import.meta.url));
const fixturePath = resolve(here, '../mocks/chat/send-message-success.json');
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));

const result = mapChatResponse(fixture);

assert.equal(result.assistantMessage.role, 'assistant');
assert.equal(result.conversationId, 12);
assert.equal(result.userMessage.role, 'user');
assert.equal(result.sources.length, 0);

console.log('chat adapter contract ok');
