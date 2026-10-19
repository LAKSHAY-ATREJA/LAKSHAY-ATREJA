import { once } from 'node:events';
import type { AddressInfo } from 'node:net';
import { WebSocket } from 'ws';
import { createWorkspace } from './server/app.js';

function nextMessage(socket: WebSocket): Promise<Record<string, unknown>> {
  return new Promise(resolve => {
    const receive = (raw: WebSocket.RawData) => {
      const message = JSON.parse(raw.toString()) as Record<string, unknown>;
      socket.off('message', receive);
      resolve(message);
    };
    socket.on('message', receive);
  });
}

async function main() {
  const { server, wss } = createWorkspace();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = (server.address() as AddressInfo).port;
  const url = `ws://127.0.0.1:${port}/ws`;
  const first = new WebSocket(url);
  const second = new WebSocket(url);

  try {
    await Promise.all([nextMessage(first), nextMessage(second)]);

    const firstCreate = nextMessage(first);
    const secondCreate = nextMessage(second);
    first.send(
      JSON.stringify({
        type: 'create',
        cardId: 'demo-card',
        baseVersion: 0,
        title: 'Review realtime collaboration',
        column: 'todo',
      }),
    );
    const broadcasts = await Promise.all([firstCreate, secondCreate]);

    const firstMove = nextMessage(first);
    const secondMove = nextMessage(second);
    second.send(
      JSON.stringify({
        type: 'move',
        cardId: 'demo-card',
        baseVersion: 1,
        column: 'doing',
      }),
    );
    await Promise.all([firstMove, secondMove]);

    const rejected = nextMessage(first);
    first.send(
      JSON.stringify({
        type: 'rename',
        cardId: 'demo-card',
        baseVersion: 1,
        title: 'Stale title',
      }),
    );
    const rejection = await rejected;
    const health = await fetch(`http://127.0.0.1:${port}/health`).then(response =>
      response.json(),
    );

    if (broadcasts.some(message => message.type !== 'applied')) {
      throw new Error('create operation was not broadcast to both clients');
    }
    if (rejection.type !== 'rejected' || rejection.error !== 'version conflict') {
      throw new Error('stale operation was not rejected');
    }

    console.log(
      JSON.stringify(
        {
          health,
          connectedClients: 2,
          createBroadcast: 'received by both clients',
          currentColumn: 'doing',
          staleWrite: 'rejected with version conflict',
        },
        null,
        2,
      ),
    );
  } finally {
    first.terminate();
    second.terminate();
    for (const socket of wss.clients) socket.terminate();
    await new Promise<void>(resolve => server.close(() => resolve()));
  }
}

await main();
