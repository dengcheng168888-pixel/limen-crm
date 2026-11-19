#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
mkdir -p backups; chmod 700 backups
out="backups/crm-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
# SQLite backup API creates a consistent snapshot even if writes are active.
umask 077
docker compose exec -T crm python -c 'import sqlite3,sys,tempfile,os; fd,p=tempfile.mkstemp();os.close(fd);src=sqlite3.connect("/app/data/crm.sqlite3");dst=sqlite3.connect(p);src.backup(dst);dst.close();src.close();sys.stdout.buffer.write(open(p,"rb").read());os.unlink(p)' > "$out"
echo "保存至 $out; 请离线加密备份，另外安全保存 .env。"
