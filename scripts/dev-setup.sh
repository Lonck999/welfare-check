#!/usr/bin/env bash
# welfare-check 本機開發環境建置 —— 從零到能看到結果頁。
#
# 🔴 為什麼要有這支（2026-09-22）：
#    這個專案停了 40 天，重新跑起來花掉的時間幾乎全在
#    「摸索環境怎麼建」而不是「寫功能」。
#    下一次（不管是我、是你、還是 Claude Code）不該再摸索一次。
#
# ⚠️ .env.example 寫的是 Neon（雲端 Postgres），會讓人以為要先去開帳號。
#    但 src/db/client.ts 用的是 drizzle-orm/node-postgres + pg 這個標準驅動，
#    **不是 Neon 專用驅動** —— 本機 Postgres 完全可以。
#
# 用法：bash scripts/dev-setup.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PG_BIN="/opt/homebrew/opt/postgresql@16/bin"
DB_NAME="welfare_check"

echo "═══ ① Postgres ═══"
if [ ! -d "$PG_BIN" ]; then
  echo "  安裝 postgresql@16…"
  brew install postgresql@16
fi
export PATH="$PG_BIN:$PATH"

if ! pg_isready -q 2>/dev/null; then
  echo "  啟動服務…"
  brew services start postgresql@16
  sleep 4
fi
# 🔴 驗終點：不是「brew services 說 started」，是「真的連得上」
pg_isready || { echo "🔴 Postgres 起不來"; exit 1; }
echo "  ✅ Postgres 可連線"

if ! psql -lqt | cut -d'|' -f1 | grep -qw "$DB_NAME"; then
  createdb "$DB_NAME"
  echo "  ✅ 建立資料庫 $DB_NAME"
else
  echo "  ✅ 資料庫 $DB_NAME 已存在"
fi

echo
echo "═══ ② backend ═══"
cd "$REPO/backend"
if [ ! -f .env ]; then
  cat > .env <<EOF
# 本機開發用（dev-setup.sh 產生）。不進版控，見 backend/.gitignore
DATABASE_URL=postgres://$(whoami)@localhost:5432/$DB_NAME
PORT=3000
SENTRY_DSN=
NODE_ENV=
EOF
  echo "  ✅ 產生 .env"
else
  echo "  ✅ .env 已存在（不覆蓋）"
fi

[ -d node_modules ] || { echo "  安裝依賴…"; npm install --silent; }
echo "  ✅ backend 依賴就緒"

set -a; . ./.env; set +a
npx drizzle-kit push --force >/dev/null 2>&1
TABLES=$(psql -d "$DB_NAME" -At -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
echo "  ✅ 資料表 $TABLES 個"
[ "$TABLES" -ge 4 ] || { echo "🔴 資料表少於 4 個，schema 沒推成功"; exit 1; }

ROWS=$(psql -d "$DB_NAME" -At -c "SELECT count(*) FROM benefits;")
if [ "$ROWS" -lt 100 ]; then
  echo "  灌資料…"
  npm run seed
  ROWS=$(psql -d "$DB_NAME" -At -c "SELECT count(*) FROM benefits;")
fi
# 🔴 驗終點：不是「seed 說寫入完成」，是真的查得到列數
echo "  ✅ benefits $ROWS 筆"
[ "$ROWS" -ge 400 ] || { echo "🔴 資料筆數異常（預期 ~499）"; exit 1; }

# 🔴 22 縣市的最低生活費必須齊全 —— 缺一個那個縣市的查詢會整個 500
COUNTIES=$(psql -d "$DB_NAME" -At -c \
  "SELECT count(DISTINCT county) FROM benefits WHERE category_number=1;")
echo "  ✅ 最低生活費涵蓋 $COUNTIES 個縣市"
[ "$COUNTIES" -eq 22 ] || { echo "🔴 縣市不齊（$COUNTIES/22），部分查詢會 500"; exit 1; }

echo
echo "═══ ③ frontend ═══"
cd "$REPO/frontend"
[ -d node_modules ] || { echo "  安裝依賴…"; npm install --silent; }
echo "  ✅ frontend 依賴就緒（API 預設打 http://localhost:3000，不必設定）"

echo
echo "═══ 完成 ═══"
cat <<'EOF'

  開兩個終端機：

    cd backend  && set -a && . ./.env && set +a && npm run dev
    cd frontend && npm run dev

  然後開 http://localhost:5173/

  🔴 驗證「真的可以用」不是看首頁長得對，是走完 16 題看到結果頁：
     node scripts/verify-flow.mjs
EOF
