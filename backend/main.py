from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI(title="PANW Case Challenge API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to PANW Case Challenge API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/example")
async def example_endpoint():
    # Example of using environment variable
    api_key = os.getenv("API_KEY", "not-set")
    return {
        "message": "Example endpoint",
        "api_key_status": "configured" if api_key != "not-set" else "not configured"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
