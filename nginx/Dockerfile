FROM nginx:1.27-alpine

RUN apk add --no-cache openssl

COPY start.sh /start.sh

RUN chmod +x /start.sh && mkdir -p /etc/nginx/ssl

CMD ["/start.sh"]
