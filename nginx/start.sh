#!/bin/sh
set -eu

SSL_DIR="/etc/nginx/ssl"
CERT_FILE="$SSL_DIR/fullchain.pem"
KEY_FILE="$SSL_DIR/privkey.pem"
DOMAIN="${NGINX_SERVER_NAME:-adivina-quien.yepesvidev.site}"

mkdir -p "$SSL_DIR"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
  echo "[nginx] No SSL certificate found. Generating self-signed certificate for $DOMAIN"
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/CN=$DOMAIN"
fi

exec nginx -g 'daemon off;'
