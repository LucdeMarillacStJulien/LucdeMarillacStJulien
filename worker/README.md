# profile-cards worker
Caches the profile stat cards at Cloudflare's edge. The cards are still
generated hourly by [`scripts/generate_stats.py`](../scripts/generate_stats.py)
and committed to this repo — this worker only fetches, caches and serves them,
so there is no GitHub token and no rendering logic to keep in sync.
Deployed at **https://profile-cards.silentspectre.workers.dev**
Routes: `/hero.svg`, `/stats.svg`, `/languages.svg`, `/streak.svg`,
`/activity.svg`, `/snake.svg`, `/snake-dark.svg`, `/views.svg`.
Cards are cached for five minutes (the stats workflow refreshes them hourly). If GitHub is
unreachable the last cached copy is served instead (`x-card-age: stale`).
`/views.svg` is a profile view counter backed by KV and is never cached.
## Deploy
```bash
cd worker && npx wrangler deploy
```
First run opens a browser to log in to Cloudflare.
The KV namespace backing `/views.svg` is already created and bound in
`wrangler.toml`. To recreate it from scratch, run
`npx wrangler kv namespace create VIEWS` and paste the printed id in.
The README already points at the deployed URL above.
## Test the route table
```bash
node test-routes.mjs
```
