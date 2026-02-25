import { createFileRoute, Link } from '@tanstack/react-router'
import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { AppLayout } from '@/components/AppLayout'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div
        className="min-h-svh w-full flex items-center justify-center bg-white text-black"
        style={{ minHeight: '100dvh' }}
      >
        <p>Loading...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LandingPage />
  }

  return <AppLayout>{null}</AppLayout>
}

function LandingPage() {
  useEffect(() => {
    document.documentElement.style.background = '#000'
    document.documentElement.style.overflow = 'hidden'
    document.body.style.background = '#000'
    document.body.style.overflow = 'hidden'
    return () => {
      document.documentElement.style.background = ''
      document.documentElement.style.overflow = ''
      document.body.style.background = ''
      document.body.style.overflow = ''
    }
  }, [])

  return (
    <div className="h-screen h-[100dvh] bg-black flex flex-col relative overflow-hidden">
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

      <div className="relative z-10 flex flex-col w-full flex-1 min-h-0 overflow-y-auto">
        <nav className="px-8 py-8 flex-shrink-0">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="text-2xl font-semibold text-white tracking-wide">Evexía</div>
            <Link
              to="/auth/login"
              search={{}}
              className="text-white/70 hover:text-white transition-colors text-sm"
            >
              Sign In
            </Link>
          </div>
        </nav>

        <main className="flex-1 flex items-center px-8">
          <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-6">
              <h1 className="text-6xl md:text-7xl lg:text-8xl xl:text-9xl font-bold text-white leading-[1.1] tracking-tight">
                Manage with
                <br />
                <span className="text-natural">clarity</span>
              </h1>
              <p className="text-lg text-white/80 leading-relaxed max-w-md tracking-wider">
                A comprehensive platform for managing clients, services, and delivery
              </p>
            </div>

            <div className="flex flex-col items-start lg:items-end gap-4">
              <Link
                to="/auth/signup"
                className="group flex items-center gap-4 px-8 py-5 bg-black/20 backdrop-blur-sm border border-white/15 hover:bg-black/30 hover:border-white/25 text-white transition-all rounded-none"
              >
                <span className="text-lg font-medium">Get Started</span>
                <span className="text-white/50 group-hover:text-white/80 group-hover:translate-x-1 transition-all">→</span>
              </Link>
              <Link
                to="/auth/login"
                search={{}}
                className="text-white/60 hover:text-white/90 transition-colors text-sm"
              >
                Already have an account?
              </Link>
            </div>
          </div>
        </main>

        <footer className="px-8 py-8 bg-black/20 backdrop-blur-sm flex-shrink-0">
          <div className="max-w-7xl mx-auto">
            <p className="text-white/50 text-xs">© 2026 Evexía</p>
          </div>
        </footer>
      </div>
    </div>
  )
}
