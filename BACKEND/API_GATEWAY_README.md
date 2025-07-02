# API Gateway Setup

This project now uses Nginx as an API gateway to route all backend services through a single port (8090).

## Architecture

All services are now accessible through port 8090 with the following URL paths:

- **Auth Service**: `http://localhost:8090/auth/`
- **Admin Service**: `http://localhost:8090/admin/`
- **Chatbot Service**: `http://localhost:8090/chat/` (also default route)
- **Preprocess Service**: `http://localhost:8090/preprocess/`
- **ML Service**: `http://localhost:8090/ml/`

## How It Works

The Nginx reverse proxy routes requests based on the URL path prefix to the appropriate backend service. This provides several benefits:

1. **Single entry point** - All services accessible through one port
2. **Simplified client integration** - Clients only need to know one base URL
3. **Better security** - Backend services aren't directly exposed
4. **Load balancing** - Nginx can handle load balancing if needed

## Running the Services

To start all services with the API gateway:

```bash
cd BACKEND
docker-compose up -d
```

## Testing the API Gateway

A test script is provided to verify the API gateway is working correctly:

```bash
cd BACKEND
chmod +x test_api_gateway.sh
./test_api_gateway.sh
```

## Updating API Clients

If you have existing API clients, update them to use the new URL structure:

- Old: `http://localhost:8888/v1/auth/...` → New: `http://localhost:8090/auth/v1/auth/...`
- Old: `http://localhost:8091/v1/chat/...` → New: `http://localhost:8090/admin/v1/chat/...`
- Old: `http://localhost:8090/v1/chat/...` → New: `http://localhost:8090/chat/v1/chat/...`
- Old: `http://localhost:8092/internal/v1/...` → New: `http://localhost:8090/preprocess/internal/v1/...`
- Old: `http://localhost:8093/...` → New: `http://localhost:8090/ml/...`

Note that all backend services now use port 8888 internally for consistency.

## Troubleshooting

If you encounter issues with the API gateway:

1. Check Nginx logs: `docker logs de_an_nginx`
2. Verify all services are running: `docker-compose ps`
3. Test individual services directly (if needed for debugging)

## Note on API Paths

You may need to update your backend services to handle the new URL path structure. For example, if your Auth service expects requests at `/v1/auth/login`, it will now receive them at `/auth/v1/auth/login`. 