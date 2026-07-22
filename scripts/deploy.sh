#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Falta .env. Ejecutá: cp .env.example .env && nano .env"
  exit 1
fi

docker compose up -d --build
docker compose ps
echo "Aplicación iniciada. Probá localmente: curl -I http://127.0.0.1:7860"
