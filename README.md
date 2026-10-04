# SkillTracker — Skill Development Tracking SaaS Platform

**SkillTracker** is a commercial-grade, multi-tenant skill-development tracking SaaS application built with Flask, SQLAlchemy, and a Slate & Navy design system. It enables educational institutions and corporate learning environments to monitor, evaluate, and accelerate student skill acquisition.

---

## Key Features

- **Multi-Role Access**: Dedicated dashboards and workflows for **Administration**, **Mentors**, and **Students**.
- **Transparent Scoring Engine**: Weighted multi-dimensional development scores (Courses, Projects, Skill Assessments, Certificates, Mentor Feedback).
- **Administrative Control Center**: User Directory (search, filter, sort, soft-deactivate), Skill Management Catalog, System Audit Log, and CSV Report Export.
- **Operational Mentor Workspace**: Real-time "Students Requiring Attention" feed, student profiles, and task assignment workflows.
- **Production-Ready Infrastructure**: Application Factory pattern, WSGI entry point, environment-driven configuration, PostgreSQL support, Flask-Migrate schema management, and `/health` monitoring endpoint.

---

## Quickstart (Local Development)

1. **Clone & Setup Environment**:
   ```bash
   cd skill_tracker
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database & Seed Demo Data**:
   ```bash
   python seed.py
   ```

4. **Launch Application**:
   ```bash
   python app.py
   ```
   Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## Demo Accounts

- **Admin Account**: `admin@college.edu` / `password123`
- **Mentor Account**: `mentor@college.edu` / `password123`
- **Student Account**: `student@college.edu` / `password123`

---

## Health Check Endpoint

```bash
curl http://127.0.0.1:5000/health
```
Response:
```json
{
  "service": "skilltracker",
  "status": "healthy"
}
```

---

## Deployment Options

For comprehensive instructions on deploying to cloud platforms like **Railway**, **Render**, or **Docker**, please refer to [DEPLOYMENT.md](file:///c:/Users/abhin/Desktop/skill_tracker/DEPLOYMENT.md).
