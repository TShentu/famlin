#!/bin/sh
set -eu
cd /workspace/source
: "${DATABASE_URL:?Olares PostgreSQL is required}"
: "${JWT_SECRET:?A generated signing key is required}"
export NODE_ENV=development
locks=$(sha256sum package-lock.json backend/package-lock.json backend/admin/package-lock.json | sha256sum | cut -d' ' -f1)
if [ "$(cat /workspace/dependencies.sha256 2>/dev/null || true)" != "$locks" ]; then
  rm -f /workspace/dependencies.sha256
  npm ci --ignore-scripts --foreground-scripts --no-audit --no-fund
  npm run build:api-client
  (cd backend && npm ci --foreground-scripts --no-audit --no-fund)
  (cd backend/admin && npm ci --foreground-scripts --no-audit --no-fund)
  printf '%s' "$locks" > /workspace/dependencies.sha256
fi
npm run build:api-client
(cd backend && npm run db:generate && npm run db:deploy)
(cd backend/admin && npm run build)
exec node deploy/olares/scripts/watch.mjs
