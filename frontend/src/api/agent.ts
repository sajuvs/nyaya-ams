import { AGENTS, DUMMY_OUTPUT, type Agent } from '../utils/dummyData'

// Stub: replace with real API call when backend is ready
// POST /api/agent/run
export async function runAgent(
  _complaint: string,
  _files: File[],
  onStepComplete: (agentId: string) => void
): Promise<string> {
  for (const agent of AGENTS) {
    await new Promise((r) => setTimeout(r, 1800 + Math.random() * 800))
    onStepComplete(agent.id)
  }
  return DUMMY_OUTPUT
}

// Stub: replace with GET /api/prompts
export async function getAgents(): Promise<Agent[]> {
  await new Promise((r) => setTimeout(r, 300))
  return AGENTS
}

// Stub: replace with PUT /api/prompts/:id
export async function updateAgentPrompt(id: string, prompt: string): Promise<void> {
  await new Promise((r) => setTimeout(r, 300))
  const agent = AGENTS.find((a) => a.id === id)
  if (agent) agent.systemPrompt = prompt
}
