# Backend - FastAPI

## Project Structure

The backend is organized into feature-based modules:

```
backend/
├── app/               # Core application (FastAPI app, models)
├── goals/             # Savings goals feature (forecasting, storage, recommendations)
├── insights/          # Spending insights feature (pipeline, triggers, scoring)
├── spending/          # Spending analytics (classification, aggregation)
├── tests/             # Test suite
├── run.py            # Entry point for running the server
└── requirements.txt
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
uvicorn run:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
