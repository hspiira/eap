import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/')({
  component: HomePage,
  head: () => ({
    links: [
      {
        rel: 'preload',
        href: '/videos/wellness.webm',
        as: 'video',
        type: 'video/webm',
      },
    ],
  }),
})

function HomePage() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-page flex items-center justify-center">
        <div className="text-text">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LandingPage />
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-text mb-6">Dashboard</h1>
        <p className="text-text-muted">
          Welcome to Evexía. Select a section from the sidebar to get started.
        </p>
      </div>
    </AppLayout>
  )
}

function LandingPage() {
  return (
    <div className="h-screen bg-black flex relative overflow-hidden">
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 z-0 w-full h-full object-cover"
        style={{ willChange: 'transform', transform: 'translateZ(0)' }}
        aria-hidden
      >
        <source src="/videos/bg_landing.webm" type="video/webm" />
      </video>
      <div 
        className="absolute inset-0 z-0 bg-black/40 backdrop-blur-[1px]" 
        style={{ willChange: 'transform', transform: 'translateZ(0)' }}
        aria-hidden 
      />

      <div className="relative z-10 flex flex-col w-full">
        <nav className="px-8 py-8">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="text-2xl font-semibold text-white tracking-wide drop-shadow-[0_1px_2px_rgba(0,0,0,0.6)]">Evexía</div>
            <Link
              to="/auth/login"
              search={{}}
              className="text-white/70 hover:text-white transition-colors text-sm drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)]"
            >
              Sign In
            </Link>
          </div>
        </nav>

        <main className="flex-1 flex items-center px-8">
          <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-6">
              <h1 className="text-6xl md:text-7xl lg:text-8xl xl:text-9xl font-bold text-white leading-[1.1] tracking-tight drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]">
                Manage with
                <br />
                <span className="text-natural">clarity</span>
              </h1>
              <p className="text-lg text-white/80 leading-relaxed max-w-md tracking-wider drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)]">
                A comprehensive platform for managing clients, services, and delivery
              </p>
            </div>

            <div className="flex flex-col items-start lg:items-end gap-4">
              <Link
                to="/auth/signup"
                className="group flex items-center gap-4 px-8 py-5 bg-black/20 backdrop-blur-sm border border-white/15 hover:bg-black/30 hover:border-white/25 text-white transition-all"
              >
                <span className="text-lg font-medium">Get Started</span>
                <span className="text-white/50 group-hover:text-white/80 group-hover:translate-x-1 transition-all">→</span>
              </Link>
              <Link
                to="/auth/login"
                search={{}}
                className="text-white/60 hover:text-white/90 transition-colors text-sm drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)]"
              >
                Already have an account?
              </Link>
            </div>
          </div>
        </main>

        <footer className="px-8 py-8 bg-black/20 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto">
            <p className="text-white/50 text-xs drop-shadow-[0_1px_1px_rgba(0,0,0,0.5)]">© 2026 Evexía</p>
          </div>
        </footer>
      </div>
    </div>
  )
}
