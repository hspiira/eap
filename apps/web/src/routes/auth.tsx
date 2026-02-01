/**
 * Auth Layout
 * Shared layout for authentication pages (login, signup)
 * Keeps video background mounted during navigation
 */

import { createFileRoute, Outlet } from '@tanstack/react-router'

export const Route = createFileRoute('/auth')({
  component: AuthLayout,
})

function AuthLayout() {
  return (
    <div className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
      <video
        autoPlay
        loop
        muted
        playsInline
        className="fixed inset-0 w-full h-full object-cover z-0"
        style={{ willChange: 'transform', transform: 'translateZ(0)' }}
        aria-hidden
      >
        <source src="/videos/wellness.webm" type="video/webm" />
      </video>
      <div 
        className="fixed inset-0 z-[1] bg-black/40 backdrop-blur-[1px]" 
        style={{ willChange: 'transform', transform: 'translateZ(0)' }}
        aria-hidden 
      />
      <div className="relative z-10 w-full max-w-md">
        <Outlet />
      </div>
    </div>
  )
}
