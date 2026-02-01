import { HeadContent, Scripts, createRootRoute } from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { TanStackDevtools } from '@tanstack/react-devtools'

import { useEffect } from 'react'
import { AuthProvider } from '../contexts/AuthContext'
import { ThemeProvider } from '../contexts/ThemeContext'
import { TenantProvider } from '../contexts/TenantContext'
import { ToastProvider } from '../contexts/ToastContext'
import { ErrorBoundary } from '../components/common/ErrorBoundary'
import { ToastContainer } from '../components/common/ToastContainer'
import { SessionTimeoutManager } from '../components/common/SessionTimeoutManager'
import { useToast } from '../contexts/ToastContext'
import { setupGlobalErrorHandlers } from '../utils/globalErrorHandler'
import appCss from '../styles.css?url'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      {
        title: 'Evexía',
      },
    ],
    links: [
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),

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
        <ErrorBoundary>
          <ThemeProvider>
            <ToastProvider>
              <AuthProvider>
                <TenantProvider>
                  <SessionTimeoutManager>
                  <ToastWrapper>
                    {children}
                  </ToastWrapper>
                  </SessionTimeoutManager>
                </TenantProvider>
              </AuthProvider>
            </ToastProvider>
          </ThemeProvider>
        </ErrorBoundary>
        <TanStackDevtools
          config={{
            position: 'bottom-right',
          }}
          plugins={[
            {
              name: 'Tanstack Router',
              render: <TanStackRouterDevtoolsPanel />,
            },
          ]}
        />
        <Scripts />
      </body>
    </html>
  )
}

function ToastWrapper({ children }: { children: React.ReactNode }) {
  const { toasts, removeToast } = useToast()
  return (
    <>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </>
  )
}
