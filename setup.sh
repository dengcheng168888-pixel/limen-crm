#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v docker >/dev/null || { echo '请先安装 Docker Engine 和 Docker Compose 插件：https://docs.docker.com/engine/install/'; exit 1; }
docker compose version >/dev/null
if [[ ! -f .env ]]; then
  umask 077
  python3 - <<'PY'
from pathlib import Path
import secrets
s=Path('.env.example').read_text()
for k in ['CRM_ADMIN_PASSWORD','CRM_SESSION_SECRET','CRM_INGEST_TOKEN']:
    s=s.replace(k+'=', k+'='+secrets.token_urlsafe(32),1)
Path('.env').write_text(s)
PY
fi
docker compose up -d --build
docker compose ps
echo '服务仅绑定 127.0.0.1:8780。请按 README 配置 HTTPS，不要直接暴露 HTTP 或公开 .env。'
echo '管理员密码在 .env 的 CRM_ADMIN_PASSWORD 中；请通过服务器终端查看并妥善保管。'
