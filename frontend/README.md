## galley / frontend

### This Is Not A Design

This frontend exists to test and develop the API. It is functional, not precious. If you are building on galley, you are not expected — or encouraged — to build on top of this. Replace it entirely with something that reflects your project.

### Tech Stack

- Vite / React / TypeScript
- TanStack Query
- Tailwind CSS
- React Router v6

### Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Runs at `http://localhost:5173`. Expects the backend at `VITE_API_BASE_URL` (default: `http://localhost:8000`).

### Build

```bash
npm run build       # production build → dist/
npm run preview     # preview the production build locally
```

### Other Commands

```bash
npm run lint
```
