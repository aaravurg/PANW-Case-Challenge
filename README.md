# PANW Case Challenge

A full-stack application built with Next.js (frontend) and FastAPI (backend) for financial analytics, spending insights, and savings goals.

## Project Overview

This project provides:
- **Spending Analytics**: Transaction classification and aggregation
- **Insights Engine**: Automated spending insights with scoring and triggers
- **Savings Goals**: Forecasting, storage, and personalized recommendations

## Project Structure

```
PANW-Case-Challenge/
├── frontend/          # Next.js application
├── backend/           # FastAPI server
│   ├── app/          # Core application (FastAPI app, models)
│   ├── goals/        # Savings goals feature
│   ├── insights/     # Spending insights feature
│   ├── spending/     # Spending analytics
│   └── tests/        # Test suite
└── README.md         # This file
```

## Getting Started

### Prerequisites

- Python 3.8+ (for backend)
- Node.js 16+ (for frontend)
- npm, yarn, pnpm, or bun (for frontend)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
uvicorn run:app --reload
```

The API will be available at `http://localhost:8000`

#### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

3. Run the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

## Technologies Used

### Frontend
- [Next.js](https://nextjs.org) - React framework
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Tailwind CSS](https://tailwindcss.com/) - Styling

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- Feature-based architecture for scalability

## Demo

Watch the project demo and walkthrough:
[YouTube Recording](https://youtu.be/XxLfbW9oWWM)

## Development

The frontend uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a font family from Vercel.

You can start editing the page by modifying `frontend/app/page.tsx`. The page auto-updates as you edit the file.

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Learn Next.js](https://nextjs.org/learn)

## License

This project was created as part of the PANW Case Challenge.
