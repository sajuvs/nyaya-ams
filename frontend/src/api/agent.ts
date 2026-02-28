import type { Agent } from '../utils/dummyData'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Debug: Log the API URL being used
console.log('API_BASE_URL:', API_BASE_URL)
console.log('import.meta.env.VITE_API_URL:', import.meta.env.VITE_API_URL)

// Type definitions matching backend schemas
export interface Domain {
  domain_name: string
  display_name: string
  description: string
}

export interface ResearchFindings {
  summary_of_facts: string[]
  legal_provisions: string[]
  merits_score: number
  reasoning: string
  kerala_specific: string
}

export interface AgentTrace {
  agent: string
  action: string
  details: string
  timestamp: string
}

export interface StartWorkflowResponse {
  session_id: string
  stage: string
  research_findings: ResearchFindings
  agent_traces: AgentTrace[]
  message: string
}

export interface ApproveResearchResponse {
  session_id: string
  stage: string
  draft: string
  research_findings: ResearchFindings
  agent_traces: AgentTrace[]
  iteration: number
  max_iterations: number
  remaining_iterations: number
  message: string
}

export interface ReviewDraftResponse {
  session_id: string
  stage: string
  draft: string
  research_findings: ResearchFindings
  agent_traces: AgentTrace[]
  iteration: number
  max_iterations: number
  remaining_iterations: number
  message: string
}

export interface FinalizeResponse {
  session_id: string
  final_document: string
  research_findings: ResearchFindings
  review_result: Record<string, unknown>
  agent_traces: AgentTrace[]
  iterations: number
  status: string
  timestamp: string
}

export interface WorkflowStatusResponse {
  session_id: string
  stage: string
  message: string
  data: {
    created_at: string
    updated_at: string
  }
}

// API Error handling
class APIError extends Error {
  status: number
  
  constructor(status: number, message: string) {
    super(message)
    this.name = 'APIError'
    this.status = status
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new APIError(response.status, error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// Health Check
export async function checkHealth(): Promise<{ status: string; service: string; version: string }> {
  const response = await fetch(`${API_BASE_URL}/health`)
  return handleResponse(response)
}

// List Available Domains
export async function listDomains(): Promise<{ domains: Domain[]; total: number }> {
  const response = await fetch(`${API_BASE_URL}/domains`)
  return handleResponse(response)
}

// Start Legal Aid Workflow
export async function startLegalAid(grievance: string, domain: string = 'legal_ai'): Promise<StartWorkflowResponse> {
  const response = await fetch(`${API_BASE_URL}/start-legal-aid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ grievance, domain })
  })
  return handleResponse(response)
}

// Approve Research Findings
export async function approveResearch(
  sessionId: string,
  approvedResearch: ResearchFindings
): Promise<ApproveResearchResponse> {
  const response = await fetch(`${API_BASE_URL}/approve-research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      approved_research: approvedResearch
    })
  })
  return handleResponse(response)
}

// Review Draft (Refinement)
export async function reviewDraft(
  sessionId: string,
  feedback: string
): Promise<ReviewDraftResponse> {
  const response = await fetch(`${API_BASE_URL}/review-draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      feedback
    })
  })
  return handleResponse(response)
}

// Finalize Legal Aid Document
export async function finalizeLegalAid(sessionId: string): Promise<FinalizeResponse> {
  const response = await fetch(`${API_BASE_URL}/finalize-legal-aid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  })
  return handleResponse(response)
}

// Get Workflow Status
export async function getWorkflowStatus(sessionId: string): Promise<WorkflowStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/workflow-status/${sessionId}`)
  return handleResponse(response)
}

// Legacy compatibility function for existing UI
// This maps the old interface to the new workflow
export async function runAgent(
  complaint: string,
  _files: File[],
  onStepComplete: (agentId: string) => void,
  domain: string = 'legal_ai'
): Promise<string> {
  try {
    // Step 1: Start workflow (Research phase)
    onStepComplete('intake')
    const startResponse = await startLegalAid(complaint, domain)
    
    onStepComplete('legal-researcher')
    
    // Step 2: Auto-approve research (for backward compatibility)
    await approveResearch(
      startResponse.session_id,
      startResponse.research_findings
    )
    
    onStepComplete('viability-assessor')
    
    // Step 3: Auto-finalize (for backward compatibility)
    const finalResponse = await finalizeLegalAid(startResponse.session_id)
    
    onStepComplete('action-planner')
    
    // Return the final document
    return finalResponse.final_document
  } catch (error) {
    if (error instanceof APIError) {
      throw new Error(`API Error (${error.status}): ${error.message}`)
    }
    throw error
  }
}

// Stub: replace with GET /api/prompts (not implemented in backend yet)
export async function getAgents(): Promise<Agent[]> {
  // This endpoint doesn't exist in the backend yet
  // Return empty array or throw error
  throw new Error('getAgents endpoint not implemented in backend')
}

// Stub: replace with PUT /api/prompts/:id (not implemented in backend yet)
export async function updateAgentPrompt(_id: string, _prompt: string): Promise<void> {
  // This endpoint doesn't exist in the backend yet
  throw new Error('updateAgentPrompt endpoint not implemented in backend')
}

// Export APIError for error handling in components
export { APIError }
