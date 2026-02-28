import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import App from './App'
import AgentPage from './routes/index'
import PromptsPage from './routes/prompts'
import VyapaPage from './routes/vyapa'

const rootRoute = createRootRoute({ component: App })

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: AgentPage,
})

const promptsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/prompts',
  component: PromptsPage,
})

const vyapaRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/vyapa',
  component: VyapaPage,
})

const routeTree = rootRoute.addChildren([indexRoute, promptsRoute, vyapaRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
