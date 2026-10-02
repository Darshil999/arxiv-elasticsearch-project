# Deploying ArXiv Semantic Search for free

This guide takes you from the code in this repository to a live website, step by step,
for **$0/month**, using just **two platforms**: **Render** for the website and the API, and
**Qdrant Cloud** for the vector database. No step needs a credit card, and it assumes you
have never deployed a full-stack app before.

**What you will end up with**

```
Browser ──► Render static site (Next.js)  ──►  Render web service (FastAPI + model)  ──►  Qdrant Cloud
            https://<site>.onrender.com        https://<api>.onrender.com                https://<id>.cloud.qdrant.io
```

| Piece | Where | Free plan | Notes |
|---|---|---|---|
| Frontend (Next.js) | **Render static site** | Free | Exported to plain HTML/JS and served from Render's CDN. **Never sleeps.** |
| Backend API (FastAPI) | **Render web service** | Free instance (512 MB RAM, 0.1 CPU) | Docker image with the embedding model. Sleeps after 15 idle minutes. |
| Vector database | **Qdrant Cloud** | Free cluster (1 GB RAM, 4 GB disk) | 20,000 papers use well under 10% of it. |

Both Render services are defined in [`render.yaml`](render.yaml) (a Render **Blueprint**), so
one click creates the site and the API together.

> Free plans change over time. The limits below were checked in September 2026. Links to each
> provider's docs are in [Step 12](#step-12-free-tier-limitations).

---

## Step 1: Accounts you need

1. **GitHub**: <https://github.com/signup> hosts your code.
2. **Qdrant Cloud**: <https://cloud.qdrant.io> hosts the vector database. Free cluster, no card.
3. **Render**: <https://dashboard.render.com/register> runs the website and the API. Free static
   sites and free web services, no card. **Sign up with your GitHub account**, which makes connecting
   the repository one click.

You also need, on your computer:

- **Git**: <https://git-scm.com/downloads>
- **Python 3.10 or newer** (3.12 recommended): <https://www.python.org/downloads/>
  (Windows: tick *"Add python.exe to PATH"* during install)
- **Node.js 20 or newer** is only needed to run the frontend locally: <https://nodejs.org>

Check them in the VS Code terminal (**Terminal → New Terminal**):

```bash
git --version
python --version        # Windows alternative: py --version
```

---

## Step 2: Push the project to GitHub

### 2.1 Create an empty repository

1. Go to <https://github.com/new>.
2. **Repository name**: `arxiv-semantic-search` (or anything you like).
3. Choose **Public** so recruiters can see it.
4. **Do not** tick "Add a README", ".gitignore" or "license". The project already has them.
5. Click **Create repository** and copy the URL it shows, e.g. `https://github.com/<you>/arxiv-semantic-search.git`.

### 2.2 (Optional) Choose your website address

Your URLs will be `https://<service-name>.onrender.com`. The names come from [`render.yaml`](render.yaml):

```yaml
name: arxiv-semantic-search-api   # -> https://arxiv-semantic-search-api.onrender.com  (API)
name: arxiv-semantic-search       # -> https://arxiv-semantic-search.onrender.com      (website)
```

These subdomains are shared by all Render users. If a name is already taken, Render adds a random
suffix, e.g. `arxiv-semantic-search-x7k2.onrender.com`. That works fine; [Step 8](#step-8-configure-cors-and-confirm-the-urls)
shows how to handle it. For a nicer, predictable URL, make both names unique **now**, for example
`jane-arxiv-search` and `jane-arxiv-search-api`, and save the file.

### 2.3 Push the code

In the VS Code terminal, from the project root (the folder that contains `backend/`, `frontend/` and this file):

```bash
git init
git add .
git commit -m "Initial deployable version"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Replace `YOUR_REPOSITORY_URL` with the URL from 2.1. If Git asks you to log in, follow the browser prompt.

### 2.4 What gets uploaded (and what doesn't)

**Uploaded:** `backend/`, `frontend/`, `scripts/`, `data/sample/papers.jsonl` (a ~2.5 MB demo dataset),
`docs/`, `docker-compose.yml`, `render.yaml`, `.env.example`, the READMEs.

**Not uploaded**, because `.gitignore` excludes it:

| Excluded | Why |
|---|---|
| `.env`, `.env.local` | Contain your **Qdrant API key**. Anyone with that key can read, change or delete your database. |
| `.venv/`, `node_modules/`, `.next/`, `out/` | Installed dependencies and build output. They are huge and get rebuilt automatically. |
| `data/*` except `data/sample/` | Your full dataset (`data/papers.jsonl`, the multi-GB Kaggle snapshot). It is rebuilt with the scripts. |
| `backend/model-cache/` | The downloaded embedding model (90 MB). It is downloaded again automatically. |

**Why `.env` must never be committed:** a public GitHub repository is readable by everyone,
and bots scan GitHub for leaked keys within minutes. Secrets go **only** into your local `.env`
file and Render's **Environment** settings. `.env.example` is committed on purpose: it lists the
variable *names* with no secret values.

Double-check before pushing:

```bash
git status            # .env must NOT appear in the list
```

---

## Step 3: Create the free Qdrant Cloud database

### 3.1 Create the cluster

1. Open <https://cloud.qdrant.io> and log in.
2. In the left sidebar click **Clusters**, then **+ Create**.
3. Select the **Free** cluster type (1 node, 1 GB RAM, 0.5 vCPU, 4 GB disk).
4. **Cloud provider / region**: pick one close to the Render region you will use in Step 5.
   Render's free regions include *Oregon, Ohio, Virginia, Frankfurt, Singapore*, and the Blueprint
   uses Render's default, **Oregon**. Good pairings:
   - Americas: a **US** region (e.g. AWS `us-west-2` or `us-east-1`, GCP `us-east4`).
   - Europe: a **Frankfurt / europe-west** region. In that case also add `region: frankfurt` to
     **both** services in `render.yaml` and push the change.
5. Give it a name, e.g. `arxiv-search`, and click **Create**. Provisioning takes 1–3 minutes.

### 3.2 Get the cluster URL

Open the cluster from the **Clusters** list. On its overview page, copy the **Endpoint / Cluster URL**.
It looks like:

```
https://0a1b2c3d-4e5f-6789-abcd-0123456789ab.us-east4-0.gcp.cloud.qdrant.io
```

Use it **without** a trailing slash. You may drop `:6333`, since HTTPS on port 443 works too.

### 3.3 Create an API key

1. In the cluster page open the **API Keys** tab (in some layouts it's under *Access Management*).
2. Click **Create** and give it a name like `arxiv-search-backend`. Keep the default full read/write access.
3. **Copy the key immediately.** It is shown only once.

### 3.4 What to save

Put these two values somewhere private, like a password manager. **Never** put them in a committed file:

| Save as | Value |
|---|---|
| `QDRANT_URL` | the cluster URL from 3.2 |
| `QDRANT_API_KEY` | the key from 3.3 |

### 3.5 The collection (no manual work needed)

You do **not** create the collection by hand. The seeding script in Step 4 creates it with:

- **Collection name:** `arxiv_papers` (the `QDRANT_COLLECTION` setting)
- **Vector size:** `384` (the output dimension of `all-MiniLM-L6-v2`)
- **Distance metric:** `Cosine`
- **Payload indexes:** `categories`, `primary_category` (keyword), used for category filters

---

## Step 4: Populate the database

You run this **once, on your own computer, from the VS Code terminal**. It downloads paper
metadata, computes embeddings on your CPU and uploads them to Qdrant Cloud. Running it
locally is simplest: Render's free plan has no shell or one-off jobs, and your laptop is far
faster than a 0.1-CPU server.

### 4.1 Create a Python environment and install dependencies

From the project root:

**Windows (PowerShell)**

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

> If PowerShell says *"running scripts is disabled"*, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, answer `Y`, and activate again.

**macOS / Linux**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

Your prompt now starts with `(.venv)`. Every command below assumes the environment is active
and that you are in the **project root**.

### 4.2 Point the scripts at Qdrant Cloud

Copy the template and fill in your values:

```bash
# Windows PowerShell
Copy-Item .env.example .env
# macOS / Linux
cp .env.example .env
```

Open `.env` in VS Code and set:

```ini
QDRANT_URL=https://0a1b2c3d-....cloud.qdrant.io     # from Step 3.2
QDRANT_API_KEY=your-api-key                          # from Step 3.3
QDRANT_COLLECTION=arxiv_papers
```

Leave the other lines as they are. `.env` is git-ignored, so the key stays on your machine.

### 4.3 Download the demo dataset (recommended: 20,000 recent papers)

```bash
python scripts/fetch_arxiv.py --total 20000
```

This calls the public arXiv API (no account needed). It fetches the newest papers from 8 CS
categories: AI, NLP, Vision, ML, IR, Distributed Computing, Security and Robotics. Cross-listed
duplicates are removed and the result is written to `data/papers.jsonl`. It takes about **3–5 minutes**
because arXiv asks clients to pause 3 s between requests.

> **Just want to test quickly?** Skip this step. The next command falls back to the bundled
> `data/sample/papers.jsonl` (about 1,400 papers).

### 4.4 Embed and upload

```bash
python scripts/seed_database.py
```

It prints the Qdrant URL it's using, creates the collection, then shows a progress bar. On a
typical laptop CPU expect **20–100 papers/second**, so about **5–15 minutes for 20,000 papers**.
You can safely stop and re-run it: papers are keyed by arXiv id, so re-running updates them
instead of creating duplicates. To start over from scratch, add `--recreate`.

### 4.5 Verify the database contains papers

```bash
python scripts/verify_index.py
```

Expected output (titles will differ):

```
Collection 'arxiv_papers' at https://....cloud.qdrant.io holds 19,4xx papers.

Query: transformer models for natural language processing   (45.2 ms)
  [0.612] ...a relevant paper title...  (2609.xxxxx, cs.CL)
...
OK - the index is populated and searchable.
```

You can also look in the Qdrant dashboard: **Clusters → your cluster → Collections** should
list `arxiv_papers` with the point count.

### Growing the dataset later

- More papers from the API: `python scripts/fetch_arxiv.py --total 50000`, then `python scripts/seed_database.py`.
- Different topics: `python scripts/fetch_arxiv.py --categories cs.LG cs.CL stat.ML --total 30000`.
- The **full** arXiv corpus: download `arxiv-metadata-oai-snapshot.json` from
  [Kaggle](https://www.kaggle.com/datasets/Cornell-University/arxiv) into `data/`, then
  `python scripts/prepare_data.py --limit 100000` (or `--categories cs --limit 0` for all ~850k CS papers,
  like the original course project).
- **Capacity:** each paper takes about 1.5 KB of vector plus about 1.5 KB of metadata. The free 1 GB cluster
  comfortably holds **100k–200k papers**. The original 850k would need a paid cluster.

---

## Step 5: Deploy the website and the API on Render (one Blueprint)

### 5.1 Work out your two URLs

Using the names in `render.yaml` (Step 2.2), write down:

| | URL |
|---|---|
| **API URL** | `https://arxiv-semantic-search-api.onrender.com` (or `https://<your-api-name>.onrender.com`) |
| **Website URL** | `https://arxiv-semantic-search.onrender.com` (or `https://<your-site-name>.onrender.com`) |

Each service needs the *other* one's URL, which is why you write them down before creating anything.
If Render ends up adding a suffix, you correct them in Step 8.

### 5.2 Create the Blueprint

1. Open <https://dashboard.render.com> and click **+ New → Blueprint**.
2. Under *Git Provider* choose **GitHub**. If this is your first time, click **Configure account**
   and give Render access to your `arxiv-semantic-search` repository.
3. Select the repository and click **Connect**.
4. **Blueprint Name**: `arxiv-semantic-search`. **Branch**: `main`. **Blueprint Path**: `render.yaml` (default).
5. Render reads `render.yaml` and lists the two services it will create:
   - `arxiv-semantic-search-api`: **Web Service**, Docker, **Free**
   - `arxiv-semantic-search`: **Static Site**
6. It then asks for the values marked `sync: false`. Fill them in exactly:

| Service | Key | Value | Where it comes from |
|---|---|---|---|
| `arxiv-semantic-search-api` | `QDRANT_URL` | `https://0a1b2c3d-....cloud.qdrant.io` | Step 3.2 |
| `arxiv-semantic-search-api` | `QDRANT_API_KEY` | your Qdrant API key | Step 3.3 |
| `arxiv-semantic-search-api` | `FRONTEND_URL` | your **Website URL** from 5.1 | lets the website call the API (CORS) |
| `arxiv-semantic-search` | `NEXT_PUBLIC_API_URL` | your **API URL** from 5.1 | tells the website where the API is |

   Use `https://` and **no trailing slash** for both URLs.

7. Click **Deploy Blueprint** (or **Apply**).

### 5.3 What Render does now

Everything else is preconfigured in `render.yaml`, so you don't type any build or start commands:

| | API (web service) | Website (static site) |
|---|---|---|
| Root directory | `backend` | `frontend` |
| Runtime | Docker (`backend/Dockerfile`) | Static site (Node 22, from `frontend/.node-version`) |
| Build | installs Python deps, downloads the model | `npm ci && npm run build` |
| Start / publish | `uvicorn` on Render's `$PORT` (from the Dockerfile) | publishes `frontend/out` to the CDN |
| Health check | `/health` | – |
| Other env vars | `QDRANT_COLLECTION=arxiv_papers`; the image sets `EMBEDDING_THREADS=1` | – |
| First build time | **5–10 minutes** | **1–3 minutes** |

Watch progress under **Dashboard → Projects / Services → select a service → Events / Logs**. The API
is ready when its logs show `Application startup complete` and then `Embedding model ready`, and its
status turns **Live**.

> The build of the website **fails on purpose** with *"NEXT_PUBLIC_API_URL is not set"* if you left that
> value empty. Add it (Step 7) and redeploy.

---

## Step 6: Verify the backend

Replace `YOUR_API` below with your API URL (no trailing slash).

**Health:** open `https://YOUR_API/health` in your browser:

```json
{"status":"ok","vector_db":"ok","papers_indexed":19432,"detail":null}
```

`papers_indexed` should match Step 4.5. If you get `503` with `"vector_db":"unreachable"`, the
`QDRANT_URL` or `QDRANT_API_KEY` on Render is wrong. Fix them under the API service's **Environment** tab.

**API docs:** open `https://YOUR_API/docs`. You get the interactive Swagger UI.
Expand **POST /api/search → Try it out**, edit the body and click **Execute**.

**Search from a terminal:**

```bash
# macOS / Linux / Git Bash
curl -X POST https://YOUR_API/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer models for computer vision", "limit": 3}'
```

```powershell
# Windows PowerShell
Invoke-RestMethod -Method Post -Uri https://YOUR_API/api/search `
  -ContentType "application/json" `
  -Body '{"query": "transformer models for computer vision", "limit": 3}'
```

A successful response looks like:

```json
{
  "query": "transformer models for computer vision",
  "count": 3,
  "took_ms": 48.1,
  "results": [
    {
      "arxiv_id": "2609.29785",
      "title": "Lightweight Vision Transformer-Based U-Net for ...",
      "abstract": "...",
      "authors": ["..."],
      "categories": ["cs.CV"],
      "primary_category": "cs.CV",
      "published": "2026-09-24",
      "updated": "2026-09-24",
      "url": "https://arxiv.org/abs/2609.29785",
      "pdf_url": "https://arxiv.org/pdf/2609.29785",
      "score": 0.4091
    }
  ]
}
```

> The **first** request after the API has been idle can take 1–2 minutes (see Step 12). Just wait
> and retry. Afterwards searches take well under a second.

---

## Step 7: Check the frontend (static site)

1. In the Render dashboard open the **`arxiv-semantic-search`** static site.
2. Its status should be **Live**, and the URL at the top is your **website**. Click it.
3. Check its settings under **Settings** (all set by the Blueprint): *Root Directory* `frontend`,
   *Build Command* `npm ci && npm run build`, *Publish Directory* `out`.
4. Under **Environment**, the only frontend variables are:

| Key | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | your API URL, e.g. `https://arxiv-semantic-search-api.onrender.com` (**no trailing slash**) |
| `NEXT_PUBLIC_GITHUB_URL` | *(optional; add it yourself)* `https://github.com/<you>/arxiv-semantic-search`, which shows a GitHub link in the header |

> `NEXT_PUBLIC_*` values are baked into the website **when it is built**. After changing one, click
> **Save, rebuild, and deploy** (or **Manual Deploy → Deploy latest commit**) for it to take effect.
> These values are visible in the browser by design. Never put a secret in a `NEXT_PUBLIC_` variable.

---

## Step 8: Configure CORS and confirm the URLs

Browsers only let the website call the API if the API lists the website's exact address in
`FRONTEND_URL`. You entered it in Step 5.2. Now confirm both URLs are the real ones:

1. Open the **static site** in the dashboard and copy its URL (top of the page), e.g.
   `https://arxiv-semantic-search.onrender.com`.
2. Open the **API service → Environment**. `FRONTEND_URL` must be **exactly** that URL:
   `https://`, no trailing slash. If it differs (for example Render added a suffix like `-x7k2`), edit it
   and click **Save, rebuild, and deploy**. Wait until the API shows **Live** again.
   - To allow several origins, separate them with commas:
     `https://arxiv-semantic-search.onrender.com,http://localhost:3000`
3. Open the **API service** and copy its URL. On the **static site → Environment**, `NEXT_PUBLIC_API_URL`
   must be exactly that URL. If not, fix it and click **Save, rebuild, and deploy**.

Nothing else needs configuring: the API only accepts `GET`/`POST` from the listed origins, and the
website has no server-side code.

---

## Step 9: Verify the live website

Open your website URL and go through this checklist:

- [ ] The frontend loads (dark page, "ArXiv Semantic Search" title)
- [ ] The badge above the title shows **"N papers indexed"** (proves the website reaches the API)
- [ ] Typing a query and pressing **Enter** runs a search
- [ ] Clicking an example chip runs a search
- [ ] Results appear with title, authors, date, category badges and an abstract
- [ ] Similarity scores and bars are displayed
- [ ] **View on arXiv** and **PDF** open the paper on arxiv.org
- [ ] Category filters and the *Results* count selector change the results
- [ ] Browser console (F12 → Console) shows **no CORS errors**
- [ ] Mobile layout works (F12 → device toolbar, or open the URL on your phone)
- [ ] Refreshing a results page (`...onrender.com/?q=...`) shows the same results
- [ ] No secrets in the frontend: in DevTools **Sources**, search for your Qdrant key. It must not be found.
      (The website only knows the public API URL. The key lives only in the API's environment.)
- [ ] The API service's **Logs** show `POST /api/search 200` lines as you search

**Troubleshooting**

| Symptom | Fix |
|---|---|
| Console: *blocked by CORS policy* | `FRONTEND_URL` on the API doesn't exactly match the website URL (check `https`, no trailing slash, suffix) → save and redeploy the API. |
| "Could not reach the search server" | API asleep (wait a minute and retry), or `NEXT_PUBLIC_API_URL` wrong → fix it on the static site and redeploy it. |
| Website build fails: *NEXT_PUBLIC_API_URL is not set* | Add the variable on the static site's **Environment** tab and redeploy. |
| "The paper index has not been created yet" | Step 4 wasn't run against the same `QDRANT_URL` / `QDRANT_COLLECTION`. |
| `/health` returns 503 | Qdrant URL/key wrong, or the free Qdrant cluster was suspended for inactivity. Resume it in the Qdrant dashboard. |

---

## Step 10: Your final URLs

| What | URL | Where to find it |
|---|---|---|
| **Website (share this one)** | `https://<site-name>.onrender.com` | Render → static site → top of the page |
| **Backend API** | `https://<api-name>.onrender.com` | Render → web service → top of the page |
| **API docs (Swagger)** | `https://<api-name>.onrender.com/docs` | API URL + `/docs` |
| **Health check** | `https://<api-name>.onrender.com/health` | API URL + `/health` |

Put the website URL on your portfolio, LinkedIn and resume, and in the GitHub repo's
**About → Website** field.

---

## Step 11: Updating the website later

```bash
git add .
git commit -m "Improve search UI"
git push
```

- Render **auto-deploys on every push to `main`**. Because each service has a root directory, only the
  affected one rebuilds: changes under `frontend/` redeploy the website (1–3 min), and changes under
  `backend/` redeploy the API (about 5 min).
- The previous version stays live until the new one is ready. Roll back from a service's **Events** tab.
- If you edit `render.yaml` itself, Render syncs the Blueprint on push. Values marked `sync: false`
  are never overwritten, so your secrets stay as you set them.
- **Data updates are separate:** to refresh papers, re-run Step 4.3–4.4 from your computer.
  The live site picks up new papers immediately, with no redeploy needed.

---

## Step 12: Free-tier limitations

**Render: static site (website)** ([docs](https://render.com/docs/static-sites))
- Free, served from a global CDN, and **does not sleep**: the page always loads instantly.
- Uses your workspace's monthly included outbound bandwidth and build minutes, which is plenty for a portfolio.
  Usage is shown under **Workspace → Billing**.

**Render: free web service (API)** ([docs](https://render.com/docs/free))
- 512 MB RAM, 0.1 CPU. The API uses about 200 MB, and a search takes about 50–300 ms on this CPU.
- **Spins down after 15 minutes without traffic.** The next search triggers a cold start:
  the container boots and loads the model, which takes **about 1–2 minutes** on 0.1 CPU. The website
  itself still loads instantly and shows a "Waking up the search server…" notice meanwhile. It also
  pings the API as soon as the page opens, so the API is often awake by the time someone finishes typing.
- 750 free instance hours per workspace per month (enough for one service running 24/7; the static
  site doesn't use instance hours).
- Free services can be restarted at any time, have no SSH/shell and no persistent disk. This app doesn't need any of those.

**Qdrant Cloud: free cluster** ([docs](https://qdrant.tech/documentation/cloud/create-cluster/))
- 1 GB RAM, 0.5 vCPU, 4 GB disk, single node (no replication).
- **Suspended after 1 week without use, and deleted after 4 weeks of inactivity** unless you resume it
  in the dashboard. Every search counts as use, and so does the API's `/health` check.
  If it is ever deleted, create a new cluster and re-run Step 4.
- Capacity: 1 GB of RAM is roughly 1M vectors of 768 dimensions. With 384-dim vectors plus
  metadata, 100k–200k papers is a comfortable ceiling.

**Will visitors see a delay?** The page itself never; the **first search after roughly 15 idle minutes**
takes 1–2 minutes, and everything after that is fast. Before an important demo, open the site a couple
of minutes beforehand.

*Optional keep-warm:* a free cron service such as <https://cron-job.org> can request
`https://<api-name>.onrender.com/health` every 10 minutes. That keeps the API awake (24 × 31 = 744 h,
just under the 750 h allowance) and keeps the Qdrant cluster counted as active.

---

## Appendix: manual setup without the Blueprint

If you prefer clicking through the dashboard instead of using `render.yaml`, create the two services
yourself. The result is identical.

**API:** **+ New → Web Service** → connect the repo, then:

| Field | Value |
|---|---|
| Name | `arxiv-semantic-search-api` |
| Language | **Docker** |
| Branch | `main` |
| Region | near your Qdrant region |
| Root Directory | `backend` |
| Dockerfile Path | `./Dockerfile` |
| Instance Type | **Free** |
| Environment Variables | `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION=arxiv_papers`, `FRONTEND_URL` (as in Step 5.2) |
| Advanced → Health Check Path | `/health` |

There are no build or start commands to enter for Docker. Click **Deploy Web Service**.

**Website:** **+ New → Static Site** → connect the same repo, then:

| Field | Value |
|---|---|
| Name | `arxiv-semantic-search` |
| Branch | `main` |
| Root Directory | `frontend` |
| Build Command | `npm ci && npm run build` |
| Publish Directory | `out` |
| Environment Variables | `NEXT_PUBLIC_API_URL` = the API URL (optional: `NEXT_PUBLIC_GITHUB_URL`) |

Click **Deploy Static Site**, then continue with [Step 6](#step-6-verify-the-backend).
