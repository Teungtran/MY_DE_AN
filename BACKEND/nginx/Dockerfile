FROM nginx:alpine

ENV UV_HTTP_TIMEOUT=300

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8090

CMD ["nginx", "-g", "daemon off;"] 