import {afterEach, expect, it} from 'vitest';
import {once} from 'node:events';
import type {AddressInfo} from 'node:net';
import {WebSocket} from 'ws';
import {createWorkspace} from '../server/app.js';

const resources: (() => Promise<void>)[] = [];
afterEach(async () => {for (const close of resources.splice(0)) await close();});

it('broadcasts edits to both clients and rejects stale writes', async () => {
  const {server,wss} = createWorkspace();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const url = `ws://127.0.0.1:${(server.address() as AddressInfo).port}/ws`;
  const a = new WebSocket(url); const b = new WebSocket(url);
  resources.push(async () => {
    a.terminate(); b.terminate();
    for (const socket of wss.clients) socket.terminate();
    await new Promise<void>(resolve => server.close(() => resolve()));
  });
  await Promise.all([once(a,'message'),once(b,'message')]);
  const broadcast = Promise.all([once(a,'message'),once(b,'message')]);
  a.send(JSON.stringify({type:'create',cardId:'test',baseVersion:0,title:'Recruiter demo',column:'todo'}));
  for (const [raw] of await broadcast) expect(JSON.parse(raw.toString()).card.version).toBe(1);
  const changed = once(a,'message');
  a.send(JSON.stringify({type:'rename',cardId:'test',baseVersion:1,title:'Updated'}));
  await changed;
  const rejected = new Promise<any>(resolve => b.on('message',raw => {
    const message=JSON.parse(raw.toString());if(message.type==='rejected')resolve(message);
  }));
  b.send(JSON.stringify({type:'move',cardId:'test',baseVersion:1,column:'done'}));
  expect((await rejected).error).toBe('version conflict');
});
