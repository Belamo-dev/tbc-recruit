# TBC Recruit MVP

MVP Website fuer TBC Classic:
- Gildenlisting erstellen
- Spielerprofil erstellen
- Suchen und filtern
- Bewerbungen Player -> Guild

Hosting (Weg A):
- Backend: Railway + Postgres
- Frontend: Cloudflare Pages

## Lokal starten (optional)
1) Postgres starten:
   docker compose up -d

2) Backend:
   cd backend
   python -m venv .venv
   .venv\Scripts\activate   (Windows)
   pip install -r requirements.txt
   set DATABASE_URL=postgresql+psycopg://tbc:tbc@localhost:5432/tbc_recruit   (Windows CMD)
   uvicorn main:app --reload

3) Frontend:
   frontend/index.html im Browser oeffnen

## Deploy
Siehe Chat Anleitung.
