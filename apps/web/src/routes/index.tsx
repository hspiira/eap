import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return (
    <div className="min-h-screen bg-calm">
      <section className="relative py-20 px-6 text-center overflow-hidden">
        <div className="relative max-w-5xl mx-auto">
          <h1 className="text-6xl md:text-7xl font-black text-safe mb-6 [letter-spacing:-0.08em]">
            Evexía
          </h1>
          <p className="text-2xl md:text-3xl text-safe mb-4 font-light">
            Management Platform
          </p>
          <p className="text-lg text-safe-light max-w-3xl mx-auto mb-8">
            Multi-tenant platform for managing services, clients, contracts, and service delivery.
          </p>
          <div className="flex flex-col items-center gap-4">
            <Link
              to="/auth/login"
              className="px-8 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors"
            >
              Get Started
            </Link>
            <p className="text-safe-light text-sm mt-2">
              Backend API: <code className="px-2 py-1 bg-calm-dark text-safe rounded-none">http://localhost:8000</code>
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
