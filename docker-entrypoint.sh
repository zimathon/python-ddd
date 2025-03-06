#!/bin/bash

# PostgreSQLが起動するまで待機
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_NAME" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

# マイグレーションを実行
python manage.py migrate

# 開発サーバーを起動
exec "$@" 