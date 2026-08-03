# Chronicle Web

An interactive English-language product page for Chronicle — a personal journal for meaningful moments, intentional goals, and thoughtful AI reflections.

## Features

- responsive landing page for desktop and mobile;
- interactive timeline filters;
- working moment composer;
- product-focused Open Graph social card;
- Cloudflare-compatible vinext build.

## Local development

```bash
pnpm install
pnpm run dev
```

Open `http://localhost:3000` in your browser.

## Production build

```bash
pnpm run build
```

The current demo uses local React state and is not connected to the Chronicle Telegram bot backend yet.
