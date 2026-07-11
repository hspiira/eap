import { useEffect } from 'react'

import { TanStackDevtools } from '@tanstack/react-devtools'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtoolsPanel } from '@tanstack/react-query-devtools'
import { createRootRoute, HeadContent, Outlet, Scripts } from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'

import { AppBootstrap } from '../components/AppBootstrap'
import { ErrorBoundary } from '../components/ui/ErrorBoundary'
import { NotFound } from '../components/ui/NotFound'
import { ToastProvider } from '../contexts/ToastContext'
import { useThemeEffect } from '../hooks/useThemeEffect'
import { queryClient } from '../lib/query-client'
import appCss from '../styles.css?url'
import { setupGlobalErrorHandlers } from '../utils/globalErrorHandler'

export const Route = createRootRoute({
  notFoundComponent: () => <NotFound fullPage />,
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'Evexía' },
    ],
    links: [{ rel: 'stylesheet', href: appCss }],
  }),
  component: RootLayout,
  shellComponent: RootDocument,
})

function RootDocument({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    setupGlobalErrorHandlers()
  }, [])
  useThemeEffect()

  return (
    <html lang="en">
      <head>
        {/* Blocking script — must run before CSS renders to prevent theme flash */}
        <script dangerouslySetInnerHTML={{ __html: `(function(){try{var s=JSON.parse(localStorage.getItem('evexia.ui')||'{}');var p=s.theme||'system';var d=p==='dark'||(p==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.setAttribute('data-theme',d?'dark':'light');if(d)document.documentElement.classList.add('dark');}catch(e){}}())` }} />
        <HeadContent />
      </head>
      <body style={{ minHeight: '100dvh' }}>
        <QueryClientProvider client={queryClient}>
          <ToastProvider>
            <AppBootstrap />
            <ErrorBoundary>
              <div className="min-h-svh w-full" style={{ minHeight: '100dvh' }}>
                {children}
              </div>
            </ErrorBoundary>
          </ToastProvider>
          <TanStackDevtools
            config={{ position: 'bottom-right' }}
            plugins={[
              { name: 'Tanstack Router', render: <TanStackRouterDevtoolsPanel /> },
              { name: 'React Query', render: <ReactQueryDevtoolsPanel /> },
            ]}
          />
        </QueryClientProvider>
        <Scripts />
      </body>
    </html>
  )
}

function RootLayout() {
  return <Outlet />
}
