import { HeadContent, Outlet, Scripts, createRootRoute } from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { TanStackDevtools } from '@tanstack/react-devtools'
import { useEffect } from 'react'
import { ThemeProvider } from '../contexts/ThemeContext'
import { ToastProvider } from '../contexts/ToastContext'
import { AppBootstrap } from '../components/AppBootstrap'
import { ErrorBoundary } from '../components/ui/ErrorBoundary'
import { NotFound } from '../components/ui/NotFound'
import { setupGlobalErrorHandlers } from '../utils/globalErrorHandler'
import appCss from '../styles.css?url'

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

  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body style={{ minHeight: '100dvh' }}>
        <ThemeProvider>
          <ToastProvider>
            <AppBootstrap />
            <ErrorBoundary>
              <div className="min-h-svh w-full" style={{ minHeight: '100dvh' }}>
                {children}
              </div>
            </ErrorBoundary>
          </ToastProvider>
        </ThemeProvider>
        <TanStackDevtools
          config={{ position: 'bottom-right' }}
          plugins={[{ name: 'Tanstack Router', render: <TanStackRouterDevtoolsPanel /> }]}
        />
        <Scripts />
      </body>
    </html>
  )
}

function RootLayout() {
  return <Outlet />
}
