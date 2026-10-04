# SkillTracker — Production Deployment Guide

This guide details how to deploy **SkillTracker** to public cloud platforms (Railway, Render) and containerized Docker environments.

---

## 1. Prerequisites & Preparation

Ensure the following environment variables are configured in your production deployment environment:

| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `FLASK_ENV` | Yes | Set to `production` | `production` |
| `SECRET_KEY` | Yes | Cryptographically strong secret key | `super-secret-production-key-99` |
| `DATABASE_URL` | Yes (for Postgres) | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `PORT` | Optional | Web server HTTP port | `5000` or `8080` |
| `SESSION_COOKIE_SECURE` | Recommended | Enable HTTPS secure cookie flag | `True` |

---

## 2. Deploying to Railway

1. **Connect Repository**:
   - Log into [Railway.app](https://railway.app).
   - Click **+ New Project** $\rightarrow$ **Deploy from GitHub repo** $\rightarrow$ Select `skill_tracker`.

2. **Add PostgreSQL Database**:
   - In your Railway project canvas, click **+ New** $\rightarrow$ **Database** $\rightarrow$ **Add PostgreSQL**.
   - Railway generates a `DATABASE_URL` variable automatically.

3. **Configure Environment Variables**:
   - Under your Web Service settings, add:
     - `FLASK_ENV` = `production`
     - `SECRET_KEY` = `<random-32-byte-key>`
     - `SESSION_COOKIE_SECURE` = `True`

4. **Build & Start Commands**:
   - Railway will automatically detect `Procfile` and run `web: gunicorn wsgi:app`.

---

## 3. Deploying to Render

1. **Create Web Service**:
   - Log into [Render.com](https://render.com).
   - Click **New +** $\rightarrow$ **Web Service** $\rightarrow$ Connect your repository.

2. **Configure Settings**:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`

3. **Attach PostgreSQL Database**:
   - Create a **New PostgreSQL** database on Render.
   - Copy the Internal Database URL into your Web Service environment variables as `DATABASE_URL`.
   - *Note*: SkillTracker automatically normalizes `postgres://` URLs to `postgresql://`.

4. **Environment Variables**:
   - Add `FLASK_ENV=production` and `SECRET_KEY=<your-secret-key>`.

---

## 4. Deploying with Docker

### Multi-Container Deployment (Docker Compose)
To run both the SkillTracker Flask web server and PostgreSQL locally or on a VPS:

```bash
docker-compose up --build -d
```

- Web interface: **[http://localhost:5000](http://localhost:5000)**
- Database: **PostgreSQL listening on port 5432**

### Single Docker Image Build
```bash
docker build -t skilltracker:latest .
docker run -p 8080:8080 -e SECRET_KEY="mysecret" skilltracker:latest
```

---

## 5. Database Migrations (Flask-Migrate)

To manage database schema changes in production without data loss:

1. **Initialize Migration Repository** (first time setup):
   ```bash
   flask db init
   ```

2. **Generate Migration Script**:
   ```bash
   flask db migrate -m "Production release migration"
   ```

3. **Apply Migrations**:
   ```bash
   flask db upgrade
   ```

---

## 6. Security & Hardening Checklist

- [x] Debug mode disabled (`FLASK_ENV=production` & `DEBUG=False`).
- [x] Application Factory pattern decoupling app creation.
- [x] Secure HTTP-only & Lax SameSite session cookies enabled.
- [x] Database URL scheme auto-corrected for SQLAlchemy 1.4+.
- [x] Standardized 400, 403, 404, 500 server-side error handling preventing debug trace leakage.
- [x] Health check endpoint `GET /health` available for automated uptime monitors.
