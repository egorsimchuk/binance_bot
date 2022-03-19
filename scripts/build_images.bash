#!/scripts/bash

set -e

export tag="1.0"
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

mkdir -p data/docker_images/${tag}

docker build -t binance-bot/db-migrations:${tag} -f Dockerfile.migrations .
docker save -o data/docker_images/${tag}/db-migrations-${tag}.tar binance-bot/db-migrations:${tag}
