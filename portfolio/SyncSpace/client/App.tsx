import {useEffect, useRef, useState, type FormEvent} from 'react';
import type {Card, Operation} from '../shared/model.js';
import './style.css';

export default function App() {
  const [cards, setCards] = useState<Card[]>([]);
  const [online, setOnline] = useState(false);
  const [notice, setNotice] = useState('');
  const [title, setTitle] = useState('');
  const ws = useRef<WebSocket | null>(null);
  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const host = location.port === '5173' ? `${location.hostname}:8080` : location.host;
    const socket = new WebSocket(`${proto}://${host}/ws`);
    ws.current = socket;
    socket.onopen = () => setOnline(true);
    socket.onclose = () => {setOnline(false); setNotice('Disconnected. Refresh to rejoin the workspace.');};
    socket.onmessage = event => {
      const message = JSON.parse(event.data);
      if (message.type === 'snapshot') setCards(message.cards);
      if (message.type === 'applied') setCards(current => [...current.filter(c => c.id !== message.card.id), message.card]);
      if (message.type === 'rejected') setNotice(`Update rejected: ${message.error}. The latest board has been loaded.`);
    };
    return () => {socket.onclose = null; socket.close();};
  }, []);
  function send(op: Operation) {
    if (ws.current?.readyState !== WebSocket.OPEN) return setNotice('Connect before editing.');
    setNotice(''); ws.current.send(JSON.stringify(op));
  }
  function create(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    send({type: 'create', cardId: crypto.randomUUID(), baseVersion: 0, title: title.trim(), column: 'todo'});
    setTitle('');
  }
  return <main>
    <header><div><span className="eyebrow">A COLLABORATIVE WORKSPACE</span><h1>SyncSpace<span>.</span></h1></div><span className={`status ${online ? 'online' : ''}`}>{online ? '● Connected' : '○ Offline'}</span></header>
    <section className="intro"><div><h2>A shared board.<br/>One current version.</h2><p>Open this page in two tabs. Add, rename or move a card and watch both boards update.</p></div><aside>DEMO NOTE<br/><p>Shared, in-memory workspace. Use sample tasks; restarting the server clears the board.</p></aside></section>
    <form onSubmit={create}><label htmlFor="new-title">New task</label><div className="add"><input id="new-title" value={title} maxLength={160} onChange={e => setTitle(e.target.value)} placeholder="What needs doing?"/><button disabled={!online || !title.trim()}>Add task →</button></div></form>
    {notice && <p role="alert" className="notice">{notice}</p>}
    <section className="board" aria-label="Task board">{['todo', 'doing', 'done'].map((column, i) => <div className="column" key={column}><h3>{['To do', 'In progress', 'Done'][i]}<span>{cards.filter(c => c.column === column).length}</span></h3>{cards.filter(c => c.column === column).map(card => <article key={card.id}><input aria-label={`Rename ${card.title}`} defaultValue={card.title} key={`${card.id}-${card.version}`} maxLength={160} disabled={!online} onBlur={e => {if (e.target.value.trim() && e.target.value !== card.title) send({type: 'rename', cardId: card.id, baseVersion: card.version, title: e.target.value.trim()});}}/><footer><small>Version {card.version}</small><select aria-label={`Move ${card.title}`} value={card.column} disabled={!online} onChange={e => send({type: 'move', cardId: card.id, baseVersion: card.version, column: e.target.value})}><option value="todo">To do</option><option value="doing">In progress</option><option value="done">Done</option></select></footer></article>)}{!cards.some(c => c.column === column) && <p className="empty">No tasks here yet</p>}</div>)}</section>
    <p className="footnote">Edits use version checks. Stale updates are rejected so another person's work is preserved.</p>
  </main>;
}
