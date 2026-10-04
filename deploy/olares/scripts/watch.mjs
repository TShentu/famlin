import { existsSync, unlinkSync } from 'node:fs';
import { spawn } from 'node:child_process';
const children = [];
let stopping = false;
const restartMarker = '/workspace/devops-restart';
// Cleared only after bootstrap has installed changed locks and built the admin UI.
if (existsSync(restartMarker)) unlinkSync(restartMarker);
setInterval(() => { if (existsSync(restartMarker)) stop(0); }, 2000);
function stop(code) {
  if (stopping) return;
  stopping = true;
  for (const child of children) { try { process.kill(-child.pid, 'SIGTERM'); } catch {} }
  setTimeout(() => process.exit(code), 500);
}
for (const [cwd, args] of [
  ['packages/api-client', ['run', 'build', '--', '--watch']],
  ['backend/admin', ['exec', 'vite', '--', 'build', '--watch']],
  ['backend', ['run', 'dev', '--', '--legacy-watch']],
  ['web', ['run', 'dev', '--', '--host', '0.0.0.0', '--strictPort']],
]) {
  const child = spawn('npm', args, { cwd, stdio: 'inherit', detached: true });
  children.push(child);
  child.on('error', err => { console.error(err); stop(1); });
  child.on('exit', code => { if (!stopping) stop(code || 1); });
}
process.on('SIGTERM', () => stop(0));
process.on('SIGINT', () => stop(0));
