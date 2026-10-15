# profile-cards worker

Caches the profile stat cards at Cloudflare's edge. The cards are still
generated hourly by [`scripts/generate_stats.py`](../scripts/generate_stats.py)
and committed to this repo — this worker only fetches, caches and serves them,
so there is no GitHub token and no rendering logic to keep in sync.

Deployed at **https://profile-cards.silentspectre.workers.dev**

Routes: `/banner.svg`, `/stats.svg`, `/languages.svg`, `/streak.svg`,
`/activity.svg`, `/snake.svg`, `/snake-dark.svg`, `/views.svg`.

Cards are cached for one hour, in step with the stats workflow. If GitHub is
unreachable the last cached copy is served instead (`x-card-age: stale`).
`/views.svg` is a profile view counter backed by KV and is never cached.

## Deploy

```bash
cd worker && npx wrangler deploy
```

First run opens a browser to log in to Cloudflare. It prints the deployed URL,
e.g. `https://profile-cards.<your-subdomain>.workers.dev`.

## Point the README at it

Replace the relative card paths with the worker URL:

```bash
sed -i 's#\./assets/\(stats\|languages\|streak\)\.svg#https://profile-cards.<your-subdomain>.workers.dev/\1.svg#g' ../README.md
```

## Test the route table

```bash
node test-routes.mjs
```
