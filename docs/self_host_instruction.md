# AgentBeats Self-Hosting Guide

This guide explains how to self-host AgentBeats services including backend (with MCP), and frontend.

## Prerequisites

- Node.js and npm
- Python 3.11+
- AgentBeats CLI installed
- pm2 and nginx (for production deployment)

## Installation Frontend

First, install frontend dependencies:
```bash
agentbeats install_frontend
```

## Deployment Options

#### Option 1: Local Development (No Authentication)

For quick local testing without login requirements:
```bash
agentbeats deploy --dev_login
```

This runs both frontend and backend on localhost. You can specify custom host and port (see CLI documentation for details). The `--dev_login` parameter skips authentication flow.

#### Option 2: Local Development (With Authentication)

1. Configure Supabase environment by creating a `.env` file in the project root:
```env
SUPABASE_URL=Your Supabase URL
SUPABASE_ANON_KEY=Your Supabase Anon Key

VITE_SUPABASE_URL=Your Supabase URL
VITE_SUPABASE_ANON_KEY=Your Supabase Anon Key
```

2. Run with authentication enabled:
```bash
agentbeats deploy
```

This enables the authentication system with GitHub OAuth support.

#### Option 3: Production Server Deployment

1. Configure Supabase environment variables (same as Option 2)

2. Install pm2 globally:
```bash
npm install -g pm2
```

3. Build and deploy:
```bash
agentbeats deploy --mode build
```

This will:
- Start the backend server
- Build the frontend for production
- Launch PM2 to manage the frontend process (runs on localhost:3000 by default)

4. Configure nginx reverse proxy using the following template:

```nginx
# AgentBeats Nginx Configuration Template
# Replace placeholders with actual values before use

# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name YOUR_DOMAIN_NAME;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN_NAME;

    ssl_certificate /path/to/ssl/cert/fullchain.pem;   # e.g., /etc/letsencrypt/live/YOUR_DOMAIN_NAME/fullchain.pem
    ssl_certificate_key /path/to/ssl/cert/privkey.pem; # e.g., /etc/letsencrypt/live/YOUR_DOMAIN_NAME/privkey.pem
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:BACKEND_PORT/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Frontend (PM2 or any Node.js process)
    location / {
        proxy_pass http://127.0.0.1:PM2_PORT; # by default 3000
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Block access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}
```
