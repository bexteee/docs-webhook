# docs-webhook

Flask webhook receiver that automates documentation deployment whenever a pull request is merged.

## The problem

Documentation drifts out of sync with code because updating it is a manual, easy-to-forget step. This project closes that gap: when a PR is merged, a GitHub Action generates a documentation summary via the Anthropic API, commits it, and triggers this webhook to rebuild and deploy the site — no manual step required.

## Architecture

```
PR merged → GitHub Action
    → fetches PR diff via GitHub REST API
    → calls Claude API to generate a doc summary
    → commits the new markdown to the docs repo
    → sends an authenticated POST to this webhook

This webhook (running on a DigitalOcean Droplet):
    → validates the request via a shared secret (HMAC comparison)
    → runs `git pull` on the docs repo
    → runs `mkdocs build`
    → atomically swaps the new build into the Nginx-served directory
```

## Key technical decisions

- **Constant-time secret comparison** — uses `hmac.compare_digest()` instead of `==` to avoid timing-attack leakage when validating the webhook secret.
- **No shell injection surface** — all subprocess calls use argument lists (`subprocess.run(["git", "pull"])`), never `shell=True` with interpolated strings.
- **Atomic deploy** — instead of deleting and rebuilding the live directory in place, the new build is assembled in a temporary folder and swapped in with `os.rename()`, minimizing the window where the site could serve a broken or partial state.
- **Fails loud, not silent** — deploy errors are caught, returned in the HTTP response (500) with the underlying exception message, and never silently swallowed.

## Stack

- Flask + Gunicorn (WSGI production server)
- systemd (process management / auto-restart on boot)
- DigitalOcean Droplet (Ubuntu) + Nginx
- MkDocs for static site generation
- GitHub Actions + Anthropic API (upstream, in the docs repo)

## Setup (local development)

```bash
git clone https://github.com/bexteee/docs-webhook.git
cd docs-webhook
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

Create a `.env` file (never committed — see `.gitignore`):

```
WEBHOOK_SECRET=your-secret-here
```

Run locally:

```bash
python app.py
```

## Deployment

Runs in production via Gunicorn, managed by systemd, on a DigitalOcean Droplet behind Nginx. See `docs-webhook.service` for the unit file.

```bash
sudo systemctl daemon-reload
sudo systemctl start docs-webhook
sudo systemctl enable docs-webhook
sudo systemctl status docs-webhook
```
