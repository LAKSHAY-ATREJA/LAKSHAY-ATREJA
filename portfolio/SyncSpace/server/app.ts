import express from 'express';
import {createServer} from 'node:http';
import {resolve} from 'node:path';
import {WebSocketServer, WebSocket} from 'ws';
import {z} from 'zod';
import {apply, type Card} from '../shared/model.js';

const common = {cardId: z.string().min(1).max(100), baseVersion: z.number().int().nonnegative()};
const column = z.enum(['todo', 'doing', 'done']);
const Op = z.discriminatedUnion('type', [
  z.object({...common, type: z.literal('create'), title: z.string().trim().min(1).max(160), column}),
  z.object({...common, type: z.literal('rename'), title: z.string().trim().min(1).max(160)}),
  z.object({...common, type: z.literal('move'), column}),
]);

export function createWorkspace() {
  const app = express();
  const server = createServer(app);
  const wss = new WebSocketServer({server, path: '/ws', maxPayload: 8192});
  const cards = new Map<string, Card>();
  const snapshot = () => ({type: 'snapshot', cards: [...cards.values()]});
  wss.on('connection', ws => {
    ws.send(JSON.stringify(snapshot()));
    ws.on('message', raw => {
      try {
        const card = apply(cards, Op.parse(JSON.parse(raw.toString())));
        const payload = JSON.stringify({type: 'applied', card});
        for (const client of wss.clients) if (client.readyState === WebSocket.OPEN) client.send(payload);
      } catch (error) {
        ws.send(JSON.stringify({type: 'rejected', error: error instanceof Error ? error.message : 'Invalid operation'}));
        ws.send(JSON.stringify(snapshot()));
      }
    });
  });
  app.get('/health', (_, res) => res.json({status: 'ok', clients: wss.clients.size}));
  app.use(express.static(resolve(process.cwd(), 'dist')));
  return {app, server, wss};
}
