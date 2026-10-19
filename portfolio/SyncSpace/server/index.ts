import {createWorkspace} from './app.js';
const port = Number(process.env.PORT ?? 8080);
createWorkspace().server.listen(port, '0.0.0.0', () => console.log(`SyncSpace: http://localhost:${port}`));
