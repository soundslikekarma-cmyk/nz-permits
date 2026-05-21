# Backend — NZ Heavy Haulage Permits

FastAPI service for the NZ Heavy Haulage Permits MVP.

## Setup (Windows PowerShell)

From the `backend/` directory:

```powershell
# Create a virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy the example env file
Copy-Item .env.example .env

# Run the dev server (auto-reload)
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://127.0.0.1:8000.

## Tests

```powershell
pytest
```
