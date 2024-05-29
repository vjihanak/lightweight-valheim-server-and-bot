#!/bin/bash
SERVER_DATA = "$HOME/valheim-server/data"
mkdir -p $SERVER_DATA
docker run -d \
  --name valheim-server \
  --cap-add=sys_nice \
  -p 2456/udp \
  -v ~/world/location:/home/valheim/provided_world \
  -v $SERVER_DATA:/home/valheim/valheim-server \
  -e SERVER_NAME="My server" \
  -e SERVER_PORT=2456 \
  -e SERVER_PASSWORD="secret" \
  -e WORLD_NAME="worldname" \
  -e TG_API_TOKEN="your:token" \
  -e TG_CHAT_ID="chatid" \
  vjihanak/lightweight-valheim-server-and-bot
