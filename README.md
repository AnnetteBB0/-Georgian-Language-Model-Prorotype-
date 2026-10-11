# CGC Frontend

Minimal paste-and-check UI for the Georgian Language Checker API.

## Run locally

Start the backend first:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

Then serve the frontend from this folder:

```bash
cd frontend
python3 -m http.server 5173
```

Open http://127.0.0.1:5173

The UI calls `http://127.0.0.1:8000/v1/check` by default. To point at another API host, set
`window.CGC_API_URL` before `app.js` loads.

## What it does

- Paste Georgian text into the editor
- Toggle spelling and grammar checks
- Underline issues directly in the text
- Show issue cards with one-click replacement suggestions
- Display engine status and rule information from integrated grammar systems (Rules/, grammar2/, georgian_grammar/)
