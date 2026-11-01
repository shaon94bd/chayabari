# Chayabari (ছায়াবাড়ি)

A mobile-first SaaS for **fine art student batches**. A whole year-batch (say, 30 students in the Jahangirnagar University Fine Art department) shares one subscription and uses it to:

- 🖼️ **host exhibitions**: curated online shows with shareable public pages and a swipe-through "walk" mode
- 🏷️ **sell artworks**: collectors send purchase requests; the artist accepts, and they arrange payment and handover
- 🔨 **run auctions**: timed auctions with a minimum increment, a hidden reserve price, anti-sniping extension and automatic winner orders
- 💬 **communicate**: a batch group chat plus direct messages (artist ↔ artist, collector ↔ artist)

**Stack:** Python 3.11 · Django 5.0.9 · Django REST Framework · JWT auth · Vue 3 + Vite + Pinia · SQLite/MySQL. Built to run on **PythonAnywhere**: no websockets, no Celery, no Redis. Chat and auctions use polling.

## How tenancy works

```
Batch owner signs up ──► Batch created + 14-day free trial + group chat
        │
        ├─ adds classmates (one per line) ──► usernames + temporary passwords generated
        │                                     (shown once; share via WhatsApp / copy)
        │
        ├─ each classmate logs in ──► forced to set their own password
        │
        └─ pays by bKash/Nagad (TrxID) ──► admin verifies in /admin ──► plan active
```

| Role | Can do |
|---|---|
| **Owner** (1 per batch) | Everything a member can, plus add/deactivate members, reset passwords, transfer ownership, pay for the subscription, edit batch settings |
| **Member** | Upload artworks, sell, auction, curate exhibitions, chat |
| **Collector** (public signup) | Browse, request to buy, bid in auctions, message artists |

When a batch's subscription lapses, its content becomes **read-only** and its public pages are **hidden** until it renews. Nothing is deleted.

## Local development

```bash
# backend
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate          # also creates the 3 default plans
python manage.py seed_demo        # optional demo batch (password: demo-pass-123)
python manage.py createsuperuser  # for /admin (verifying payments)
python manage.py runserver        # http://127.0.0.1:8000

# frontend (another terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173 (proxies /api and /media to Django)
```

Demo logins after `seed_demo`: `demo_owner`, `nusrat`, `tanvir`, `mitu`, `sabbir` (students) and `collector`. They all use the password `demo-pass-123`.

Run the backend tests:

```bash
cd backend && python manage.py test
```

## Deploying to PythonAnywhere

See **[docs/DEPLOY_PYTHONANYWHERE.md](docs/DEPLOY_PYTHONANYWHERE.md)**. Deploy the **`backend`** branch, which contains just the Django project with `manage.py` at the top level and the built Vue app in `spa/`. After a one-time `pip install`, updating is just `git pull` + Reload: migrations, static files and the secret key are handled automatically.

## Project layout

```
backend/
  config/            settings, URLs, SPA index view
  apps/accounts/     custom User (owner/member/collector), login, profile, password change
  apps/batches/      Batch (tenant), Plan, Subscription, Payment, members admin, billing
  apps/gallery/      Artwork (+ extra photos), Exhibition
  apps/auctions/     Auction, Bid, settle_auctions command
  apps/market/       Order (purchase requests and auction wins)
  apps/messaging/    Conversation (group/direct), Message, read state
  apps/core/         permissions, image downscaling, test helpers
frontend/
  src/views/         one file per screen
  src/components/    shared UI (bottom nav, cards, sheets, image picker…)
docs/                deployment guide
```

## API overview (`/api/…`)

| Area | Endpoints |
|---|---|
| Auth | `auth/login/`, `auth/refresh/`, `auth/me/`, `auth/change-password/`, `auth/register/` (collector) |
| Batch | `signup/`, `plans/`, `batch/`, `batch/members/` (GET, POST single or `{members:[…]}`), `batch/members/<id>/`, `…/reset-password/`, `…/make-owner/`, `batch/subscription/`, `batch/subscription/checkout/`, `public/batches/<slug>/` |
| Gallery | `artworks/` (`?mine=1&batch=&artist=&for_sale=1&q=`), `artworks/<id>/images/`, `exhibitions/` (`?batch=&mine_batch=1`) |
| Auctions | `auctions/` (`?phase=live|scheduled|ended|open&mine=1`), `auctions/<id>/bid/`, `…/bids/`, `…/cancel/` |
| Orders | `orders/` (`?role=buyer|seller`), `orders/<id>/accept|reject|complete|cancel/` |
| Chat | `conversations/`, `conversations/direct/`, `conversations/unread/`, `conversations/<id>/messages/` (`?after=<id>` to poll) |

## Roadmap ideas

- Automatic payment gateway (SSLCommerz / bKash Checkout API) instead of manual TrxID verification
- Push or email notifications for bids, orders and messages
- Bangla UI translation
- Certificate of authenticity PDF for sold works
- Platform commission on sales
