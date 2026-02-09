# Environment Setup

After running `composer install`, create a `.env` file in the frontend directory with the following content:

```
APP_NAME="Report Analysis"
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost

LOG_CHANNEL=stack
LOG_LEVEL=debug

BROADCAST_DRIVER=log
CACHE_DRIVER=file
FILESYSTEM_DRIVER=local
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120

# Python API URL - Update this to point to your backend server
# For local development: http://localhost:8001
# For remote server: http://your-backend-server.com:8001
# For production: https://api.yourdomain.com
PYTHON_API_URL=http://localhost:8001
```

Then run:
```bash
php artisan key:generate
```

This will generate the APP_KEY automatically.

## Running Backend on a Different Server

### Backend Server Setup:

1. **Start the Python backend** on your server:
   ```bash
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8001
   ```

2. **Configure CORS (Optional)** - If you want to restrict which frontend servers can access:
   ```bash
   # In backend directory, set environment variable:
   export CORS_ORIGINS="http://your-frontend-server.com,http://localhost:8000"
   # Or allow all (default):
   export CORS_ORIGINS="*"
   ```

3. **Update Frontend `.env`**:
   ```env
   PYTHON_API_URL=http://your-backend-server-ip:8001
   # Or with domain:
   PYTHON_API_URL=https://api.yourdomain.com
   ```

4. **Restart Laravel** to pick up the new environment variable:
   ```bash
   php artisan config:clear
   php artisan cache:clear
   ```

### Testing the Connection:

You can test if the backend is accessible from your frontend server:
```bash
curl http://your-backend-server:8001/api/analyze
```

If you get a response (even an error about missing parameters), the connection is working!

