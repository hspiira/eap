import { HeadContent, Outlet, Scripts, createRootRoute } from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { TanStackDevtools } from '@tanstack/react-devtools'
import { useEffect } from 'react'
import { AuthProvider } from '../contexts/AuthContext'
import { ThemeProvider } from '../contexts/ThemeContext'
import { TenantProvider } from '../contexts/TenantContext'
import { ToastProvider } from '../contexts/ToastContext'
import { setupGlobalErrorHandlers } from '../utils/globalErrorHandler'
import appCss from '../styles.css?url'

export const Route = createRootRoute({
  notFoundComponent: () => (
    <div className="min-h-screen flex items-center justify-center bg-[#E6E0D7] text-[#5A626A]">
      <p>Page not found</p>
    </div>
  ),
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
      <body>
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <TenantProvider>
                {children}
              </TenantProvider>
            </AuthProvider>
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
