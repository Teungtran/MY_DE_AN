# ---------- Build stage ----------
# Use Node 20 to match React Router / Vite requirements
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files first for caching
COPY package*.json ./

# Install dependencies (clean CI install)
RUN npm ci

# Copy source code
COPY . .

# Build the application (Vite outputs to "dist" by default)
RUN npm run build

# ---------- Production stage ----------
FROM nginx:alpine AS production

# Copy build artifacts to nginx html directory
# Vite outputs to "build" directory as configured in vite.config.ts
COPY --from=builder /app/build /usr/share/nginx/html

# Configure nginx for SPA routing + API proxy
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # SPA fallback - serve index.html for all routes \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Proxy backend API calls \
    location ~ ^/(auth|ml|chat|admin|preprocess)/ { \
        proxy_pass http://nginx:8090; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_read_timeout 300s; \
        proxy_connect_timeout 75s; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
