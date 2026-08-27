# Deploying the Shtrader LA engine as a public API

The web console is a frontend; its "brain" is the Python FastAPI engine in
`shtrader_la/api/`. To make a hosted preview (or the Lovable URL) work from any
browser, you deploy the **engine** to a public HTTPS host, then point the console
at it.

Good news: the engine needs **no GGUF model** — it runs fully offline with the
deterministic `StubProvider`, so it feels like a small, cheap web service.

## 1. What you ship

Only `shtrader_la/` (stdlib core + FastAPI bridge) plus `requirements.txt`.
`deploy/engine.Dockerfile` + root `.dockerignore` package exactly that.

## 2. Deploy the engine (pick one host)

### Option A — Any Docker host (Render / Railway / Fly.io / VPS)

Build the image from the repo root:

```sh
docker build -f deploy/engine.Dockerfile -t shtrader-la-engine .
docker run --rm -p 8000:8000 shtrader-la-engine
```

- Render: new "Web Service" → connect repo → Root Directory `/` →
  Build command ignored, Start command `python -m uvicorn shtrader_la.api.app:app --host 0.0.0.0 --port 8000`.
- Railway / Fly: it's a standard container; expose port 8000.
- On Render/Railway set env `SHTRADER_API_ALLOWED_ORIGINS=*` (already the default).

### Option B — Fly.io

```sh
fly launch  # from repo root; answer to serve /app via the Dockerfile
fly deploy
```

### Option C — Serve it near you (LAN) without the cloud

For demos where the viewer can reach your machine:
`.venv\Scripts\python -m uvicorn shtrader_la.api.app:app --host 0.0.0.0 --port 8000`
then point the console at `http://<your-LAN-ip>:8000`.

The API stays offline-deterministic and takes no secrets.

## 3. Point the web console at the public engine

The console resolves the engine URL in this order:

1. **Runtime override** (persisted) — the "Engine endpoint" field at the bottom
   of the chat input: paste the public URL, hit Apply. Works immediately, no rebuild.
2. **Build-time env** — set `VITE_SHTRADER_API_URL` (see `.env.example`) when you
   build/deploy the frontend, so the default is your public engine.
3. Stable default `http://127.0.0.1:8000` (local dev via `npm run start:all`).

## 4. Verify after deploying

```sh
curl https://<your-engine-host>/health
curl -X POST https://<your-engine-host>/api/v1/chat \
  -H 'content-type: application/json' \
  -d '{"query":"Calculate my position size for EUR/USD with a $5,000 account, 2% risk and 50 pip stop.","session_id":"demo"}'
```

You should get `intent: position_sizing` with a computed lot size. CORS is `*` by
default, so the deployed browser page can load it from any origin.

## Notes

- The engine keeps per-`session_id` memory in the process; for heavy concurrent
  use scale out behind a load balancer with sticky sessions or run one instance.
- The local Llama GGUF model stays on your machine — this hosted engine returns
  deterministic tool + knowledge answers (no language-model narration) and makes
  zero cloud AI calls.