# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```bash
# create a new project in the current directory
npx sv create

# create a new project in my-app
npx sv create my-app
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.

# Nginx Reverse Proxy Example for AgentBeats

This example shows how to set up nginx to serve your frontend and proxy API requests to your backend.

## Example nginx config

```
server {
    listen 80;
    server_name nuggets.puppy9.com;

    # Serve frontend static files (adjust root as needed)
    root /path/to/frontend/dist;
    index index.html;

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://localhost:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Fallback for SPA (if using client-side routing)
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- Replace `/path/to/frontend/dist` with the actual path to your built frontend files.
- Make sure your backend is running on `localhost:9000`.
- Reload nginx after updating the config: `sudo systemctl reload nginx` or `sudo nginx -s reload`.

## HTTPS (Recommended)

For HTTPS, use [certbot](https://certbot.eff.org/) or another tool to obtain a certificate and update the `listen` and `ssl_certificate` directives accordingly.

---

This setup ensures your frontend and backend work together securely and efficiently in production.
