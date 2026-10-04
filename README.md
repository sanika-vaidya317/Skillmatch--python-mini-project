# SkillMatch (Python conversion, Phase 1)

Phase 1 of converting the SkillMatch event volunteering app from a React frontend to server-rendered Python (FastAPI + Jinja2 + HTMX).

Tools used: the base app was generated with Replit AI and modified with Emergent AI; the Python conversion uses GitHub Copilot, then reviewed and tested by the team.

Phase 1 contains: Jinja2 templates (base layout, login/register page, flash messages, icon macros), static CSS, vendored htmx, and HTML login/register/logout routes on the existing FastAPI backend.

To run: install backend/requirements.txt, create backend/.env with MONGO_URL, DB_NAME and JWT_SECRET (at least 32 characters), then from backend/ run: uvicorn server:app --port 8001