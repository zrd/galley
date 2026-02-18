# Self-Publishing Platform Frontend

A minimal React frontend for testing and development of the self-publishing platform API.

## Tech Stack

- React 18 with TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Router v6 (routing)
- TanStack Query (React Query) for API data fetching

## Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Configure the API URL in `.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

4. Start the development server:

```bash
npm run dev
```

The app will be available at http://localhost:5173

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and endpoint functions
│   │   ├── client.ts  # Base HTTP client with auth
│   │   ├── auth.ts    # Auth endpoints
│   │   ├── manuscripts.ts
│   │   └── ebooks.ts
│   ├── components/    # Reusable UI components
│   │   ├── Layout.tsx
│   │   ├── Navbar.tsx
│   │   └── ProtectedRoute.tsx
│   ├── hooks/         # Custom React hooks
│   │   ├── useAuth.tsx
│   │   └── useManuscripts.ts
│   ├── pages/         # Page components
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── ManuscriptForm.tsx
│   │   └── ManuscriptDetail.tsx
│   ├── types/         # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx        # Main app with routes
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles (Tailwind)
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Features

- **Authentication**: Login and registration with JWT tokens
- **Dashboard**: List all manuscripts with state badges
- **Create Manuscript**: Upload form with file selection and format detection
- **View/Edit Manuscript**: Detail page with edit mode
- **Generate Ebook**: Convert ready manuscripts to EPUB/PDF

## API Integration

The frontend expects the backend to be running at the URL specified in `VITE_API_BASE_URL`.

### CORS

Make sure your FastAPI backend allows CORS from the frontend origin. Add to your backend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Notes

- Authentication tokens are stored in localStorage
- The app uses a Vite proxy to forward `/api` requests to the backend (configurable in vite.config.ts)
- All protected routes redirect to login if not authenticated
