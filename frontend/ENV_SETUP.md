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

# Python API URL
PYTHON_API_URL=http://localhost:8001
```

Then run:
```bash
php artisan key:generate
```

This will generate the APP_KEY automatically.

