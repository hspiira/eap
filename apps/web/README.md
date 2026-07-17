# Evexía Frontend

Frontend application for the Evexía platform.

## Tech Stack

- **Framework**: [TanStack Start](https://tanstack.com/start) (React)
- **Routing**: TanStack Router
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **Build Tool**: Vite

## Getting Started

### Prerequisites

- Node.js 22+ (CI builds on 22 LTS)
- pnpm (the only supported package manager — the repo pins it via `packageManager`
  in `package.json` and `pnpm-lock.yaml` is the source of truth; do not use npm or yarn)
- Backend API running at `http://localhost:8000`

### Installation

```bash
pnpm install
```

### Development

```bash
pnpm dev
```

The application will be available at `http://localhost:3000`

### Building for Production

```bash
pnpm build
```

### Testing

```bash
pnpm test         # unit tests
pnpm lint         # eslint
pnpm typecheck    # tsc --noEmit
```

These four commands are exactly what CI runs on every push and pull request
(`.github/workflows/ci.yml`) — run them before pushing.

## Project Structure

```
src/
├── api/              # API client and endpoints
├── components/       # React components
│   ├── common/      # Reusable components
│   ├── features/    # Feature-specific components
│   └── layout/      # Layout components
├── hooks/           # Custom React hooks
├── routes/          # TanStack Router routes
├── store/           # State management
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Evexía
VITE_APP_ENV=development
```

## Documentation

- [Frontend Development Guide](./docs/FRONTEND_DEVELOPMENT_GUIDE.md) - Complete API and implementation guide
- [Implementation Plan](./docs/IMPLEMENTATION_PLAN.md) - Step-by-step development plan

## Backend API

The frontend connects to a FastAPI backend (same API locally and deployed). API documentation:

- **Local**: Swagger UI `http://localhost:8000/docs` · ReDoc `http://localhost:8000/redoc`
- **Deployed**: [ReDoc](https://eap-ten.vercel.app/redoc) · use for reference when running local backend

## Features

- Multi-tenant support
- Authentication & authorization
- Client management
- Person management (employees, dependents, service providers)
- Contract management
- Service catalog and delivery
- Document management
- KPI tracking
- Audit logging

## Development Guidelines

- Use TypeScript strict mode
- Follow the project structure conventions
- Write tests for critical functionality
- Document components and functions
- Follow the implementation plan phases

## License

[Add license information]
