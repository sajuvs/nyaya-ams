# Nyaya-Flow API Documentation for Frontend Developers

## Overview
This document provides a complete guide for integrating the Nyaya-Flow Legal Aid Platform frontend with the backend API. The system uses a **Human-in-the-Loop (HITL)** workflow where users review and approve outputs at each stage.

---

## Base URL
```
http://localhost:8000/api/v1
```

---

## Workflow Stages

The legal aid generation follows a **4-stage workflow**:

1. **Start Workflow** → Research findings returned
2. **Approve Research** → Draft generated
3. **Review Draft** (repeatable up to 3 times) → Refined draft
4. **Finalize** → Final approved document

```
┌─────────────┐
│   User      │
│  Submits    │
│ Grievance   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Stage 1: Research Phase            │
│  POST /start-legal-aid              │
│  Returns: research findings         │
└──────┬──────────────────────────────┘
       │
       ▼  Human reviews & approves
       │
┌─────────────────────────────────────┐
│  Stage 2: Drafting Phase            │
│  POST /approve-research             │
│  Returns: initial draft             │
└──────┬──────────────────────────────┘
       │
       ▼  Human reviews draft
       │
       ├─── Needs changes? ───┐
       │                      │
       │                      ▼
       │              ┌───────────────────┐
       │              │  POST /review-draft│
       │              │  (max 3 times)    │
       │              └────────┬──────────┘
       │                       │
       │◄──────────────────────┘
       │
       ▼  Draft approved
       │
┌─────────────────────────────────────┐
│  Stage 3: Finalization              │
│  POST /finalize-legal-aid           │
│  Returns: final document            │
└─────────────────────────────────────┘
```

---

## API Endpoints

### 1. Health Check
**Purpose:** Verify API is running

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "Nyaya-Flow Legal Aid API",
  "version": "1.0.0",
  "agents": ["researcher", "drafter", "expert_reviewer"],
  "mode": "human-in-the-loop"
}
```

**Frontend Action:** Display connection status

---

### 2. Start Legal Aid Workflow
**Purpose:** Submit grievance and get research findings

**Endpoint:** `POST /start-legal-aid`

**Request Body:**
```json
{
  "grievance": "I purchased a defective mobile phone from a shop in Kochi. The seller refuses to provide a refund despite the warranty."
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "awaiting_research_approval",
  "research_findings": {
    "summary_of_facts": [
      "Purchased defective mobile phone in Kochi",
      "Seller refused refund despite warranty"
    ],
    "legal_provisions": [
      "Consumer Protection Act 2019, Section 35",
      "Sale of Goods Act 1930, Section 16"
    ],
    "merits_score": 8,
    "reasoning": "Strong case under consumer protection laws...",
    "kerala_specific": "Kerala Consumer Disputes Redressal Commission has jurisdiction"
  },
  "agent_traces": [
    {
      "agent": "orchestrator",
      "action": "gathering_context",
      "details": "Searching local Kerala acts...",
      "timestamp": "2024-02-27T10:00:00"
    },
    {
      "agent": "researcher",
      "action": "research_complete",
      "details": "Identified 2 legal provisions...",
      "timestamp": "2024-02-27T10:00:15"
    }
  ],
  "message": "Please review and approve the research findings to continue."
}
```

**Frontend Actions:**
1. Store `session_id` (required for all subsequent calls)
2. Display research findings in editable form:
   - Summary of facts (list)
   - Legal provisions (list)
   - Merits score (1-10 slider)
   - Reasoning (text area)
   - Kerala-specific info (text area)
3. Show agent traces in timeline/log view
4. Provide "Approve & Continue" button
5. Allow user to edit any field before approval

**Error Handling:**
- 500: Display error message, allow retry

---

### 3. Approve Research Findings
**Purpose:** Submit approved/edited research and get initial draft

**Endpoint:** `POST /approve-research`

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_research": {
    "summary_of_facts": [
      "Purchased defective mobile phone in Kochi",
      "Seller refused refund despite warranty"
    ],
    "legal_provisions": [
      "Consumer Protection Act 2019, Section 35",
      "Sale of Goods Act 1930, Section 16"
    ],
    "merits_score": 8,
    "reasoning": "Strong case under consumer protection laws...",
    "kerala_specific": "Kerala Consumer Disputes Redressal Commission has jurisdiction"
  }
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "awaiting_draft_review",
  "draft": "To: The District Consumer Forum, Kochi\n\nFrom: [INSERT NAME]\n\nSubject: Consumer Complaint under Consumer Protection Act 2019\n\n...[full legal petition]...",
  "research_findings": { /* same as approved */ },
  "agent_traces": [ /* updated traces */ ],
  "iteration": 1,
  "max_iterations": 3,
  "remaining_iterations": 2,
  "message": "Please review the draft (Iteration 1/3). Approve or provide feedback for refinement (2 refinements remaining)."
}
```

**Frontend Actions:**
1. Display draft in formatted text viewer (preserve formatting)
2. Show iteration counter: "Draft 1 of 3"
3. Show remaining refinements: "2 refinements remaining"
4. Provide two options:
   - **"Approve & Finalize"** button → Go to Step 5
   - **"Request Changes"** button → Show feedback textarea → Go to Step 4
5. Update agent traces timeline

**Error Handling:**
- 400: Invalid session or stage → Display error, redirect to start
- 500: Server error → Display error, allow retry

---

### 4. Review Draft (Refinement Loop)
**Purpose:** Provide feedback to refine the draft

**Endpoint:** `POST /review-draft`

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "feedback": "Please add more details about the warranty terms and include the purchase date placeholder."
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "awaiting_draft_review",
  "draft": "To: The District Consumer Forum, Kochi\n\n...[refined draft with changes]...",
  "research_findings": { /* same */ },
  "agent_traces": [ /* updated with refinement traces */ ],
  "iteration": 2,
  "max_iterations": 3,
  "remaining_iterations": 1,
  "message": "Please review the refined draft (Iteration 2/3). Approve or provide additional feedback (1 refinement remaining)."
}
```

**Frontend Actions:**
1. Display refined draft
2. Update iteration counter: "Draft 2 of 3"
3. Update remaining refinements: "1 refinement remaining"
4. If `remaining_iterations === 0`:
   - Disable "Request Changes" button
   - Show message: "Maximum refinements reached. Please approve or start new workflow."
5. Update agent traces

**Error Handling:**
- 400 with "Maximum iterations reached":
  - Display: "You've used all 3 refinements. Please approve the current draft or start a new workflow."
  - Disable feedback input
  - Only show "Approve & Finalize" button

---

### 5. Finalize Legal Aid Document
**Purpose:** Approve final draft and complete workflow

**Endpoint:** `POST /finalize-legal-aid`

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "final_document": "To: The District Consumer Forum, Kochi\n\n...[complete approved petition]...",
  "research_findings": { /* final research */ },
  "review_result": {},
  "agent_traces": [ /* complete workflow traces */ ],
  "iterations": 2,
  "status": "approved_by_human",
  "timestamp": "2024-02-27T10:15:00"
}
```

**Frontend Actions:**
1. Display success message: "Legal aid document generated successfully!"
2. Show final document with download options:
   - **Download as PDF**
   - **Download as DOCX**
   - **Copy to Clipboard**
3. Display complete workflow summary:
   - Total iterations: 2
   - Status: Approved by human
   - Timestamp
4. Show complete agent traces timeline
5. Provide "Start New Workflow" button
6. Clear session data

**Error Handling:**
- 400: Invalid session → Display error
- 500: Server error → Display error, allow retry

---

### 6. Get Workflow Status (Optional)
**Purpose:** Check current stage of workflow

**Endpoint:** `GET /workflow-status/{session_id}`

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "awaiting_draft_review",
  "message": "Workflow is at stage: awaiting_draft_review",
  "data": {
    "created_at": "2024-02-27T10:00:00",
    "updated_at": "2024-02-27T10:05:00"
  }
}
```

**Frontend Actions:**
1. Use for session recovery if user refreshes page
2. Redirect to appropriate stage based on `stage` value
3. Display time elapsed since creation

---

## Complete Frontend Flow

### Page 1: Grievance Submission
```
┌─────────────────────────────────────┐
│  Enter Your Legal Issue             │
│  ┌───────────────────────────────┐  │
│  │ [Large text area]             │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                                     │
│  [Submit] button                    │
└─────────────────────────────────────┘
```
**API Call:** `POST /start-legal-aid`

---

### Page 2: Research Review
```
┌─────────────────────────────────────┐
│  Research Findings                  │
│                                     │
│  Summary of Facts: (editable)       │
│  • [Fact 1]                         │
│  • [Fact 2]                         │
│                                     │
│  Legal Provisions: (editable)       │
│  • [Law 1]                          │
│  • [Law 2]                          │
│                                     │
│  Case Strength: [8/10] (slider)     │
│                                     │
│  Reasoning: (editable textarea)     │
│                                     │
│  [Approve & Continue] button        │
│                                     │
│  Agent Activity Log:                │
│  • Researcher: Analyzed grievance   │
│  • RAG Search: Found 3 documents    │
└─────────────────────────────────────┘
```
**API Call:** `POST /approve-research`

---

### Page 3: Draft Review
```
┌─────────────────────────────────────┐
│  Legal Petition Draft               │
│  Iteration: 1/3 (2 refinements left)│
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [Formatted draft display]     │  │
│  │                               │  │
│  │ To: District Consumer Forum   │  │
│  │ ...                           │  │
│  └───────────────────────────────┘  │
│                                     │
│  [Approve & Finalize]               │
│  [Request Changes]                  │
│                                     │
│  If "Request Changes" clicked:      │
│  ┌───────────────────────────────┐  │
│  │ Feedback: [textarea]          │  │
│  └───────────────────────────────┘  │
│  [Submit Feedback]                  │
└─────────────────────────────────────┘
```
**API Calls:** 
- `POST /review-draft` (if changes requested)
- `POST /finalize-legal-aid` (if approved)

---

### Page 4: Final Document
```
┌─────────────────────────────────────┐
│  ✓ Legal Aid Document Complete      │
│                                     │
│  Status: Approved by Human          │
│  Iterations: 2                      │
│  Generated: 2024-02-27 10:15        │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [Final document display]      │  │
│  └───────────────────────────────┘  │
│                                     │
│  [Download PDF] [Download DOCX]     │
│  [Copy to Clipboard]                │
│                                     │
│  [Start New Workflow]               │
│                                     │
│  Complete Workflow Timeline:        │
│  • Started: 10:00                   │
│  • Research: 10:01                  │
│  • Draft 1: 10:05                   │
│  • Draft 2: 10:10                   │
│  • Finalized: 10:15                 │
└─────────────────────────────────────┘
```

---

## State Management

### Required State Variables
```javascript
{
  sessionId: string | null,
  currentStage: 'start' | 'research' | 'draft' | 'complete',
  grievance: string,
  researchFindings: object | null,
  currentDraft: string | null,
  iteration: number,
  maxIterations: number,
  remainingIterations: number,
  agentTraces: array,
  finalDocument: object | null
}
```

### Session Persistence
- Store `sessionId` in localStorage
- On page refresh, call `GET /workflow-status/{sessionId}`
- Restore state based on current stage

---

## Error Handling Matrix

| Error Code | Scenario | Frontend Action |
|------------|----------|-----------------|
| 400 | Invalid session | Show error, redirect to start |
| 400 | Invalid stage | Show error, redirect to correct stage |
| 400 | Max iterations | Disable feedback, show finalize only |
| 404 | Session not found | Show error, redirect to start |
| 500 | Server error | Show error, provide retry button |
| Network | Connection failed | Show offline message, queue request |

---

## UI/UX Recommendations

### Loading States
- Show spinner during API calls
- Display "Analyzing grievance..." during research
- Display "Generating draft..." during drafting
- Display "Refining draft..." during refinement

### Progress Indicator
```
[●────────] Research Complete
[●●───────] Draft Generated
[●●●──────] Draft Refined (1/3)
[●●●●─────] Draft Refined (2/3)
[●●●●●────] Finalized
```

### Agent Traces Display
Show as expandable timeline:
```
▼ 10:00:00 - Orchestrator: Gathering context
  Details: Searching local Kerala acts...
▼ 10:00:15 - RAG Search: Local search complete
  Details: Retrieved 1,234 characters...
▼ 10:00:20 - Tavily Search: Web search complete
  Details: Found 3 relevant sources
```

### Validation
- Grievance: Minimum 10 characters
- Feedback: Minimum 10 characters
- Research fields: Cannot be empty

---

## Testing Checklist

- [ ] Submit grievance and receive research
- [ ] Edit research findings before approval
- [ ] Approve research and receive draft
- [ ] Request changes to draft (iteration 1)
- [ ] Request changes to draft (iteration 2)
- [ ] Request changes to draft (iteration 3)
- [ ] Verify max iterations error on 4th attempt
- [ ] Finalize approved draft
- [ ] Download final document
- [ ] Session recovery after page refresh
- [ ] Handle network errors gracefully
- [ ] Handle invalid session errors
- [ ] Display agent traces correctly

---

## Example API Call Sequence

```javascript
// 1. Start workflow
const startResponse = await fetch('/api/v1/start-legal-aid', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ grievance: userInput })
});
const { session_id, research_findings } = await startResponse.json();

// 2. User reviews and approves research
const approveResponse = await fetch('/api/v1/approve-research', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    session_id, 
    approved_research: editedResearch 
  })
});
const { draft, iteration } = await approveResponse.json();

// 3. User requests changes (optional, repeatable)
const refineResponse = await fetch('/api/v1/review-draft', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    session_id, 
    feedback: userFeedback 
  })
});
const { draft: refinedDraft } = await refineResponse.json();

// 4. User approves final draft
const finalResponse = await fetch('/api/v1/finalize-legal-aid', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id })
});
const { final_document } = await finalResponse.json();
```

---

## Support

For questions or issues:
- Backend API: Check `/docs` for interactive Swagger documentation
- Session issues: Use `GET /workflow-status/{session_id}` to debug
- Max iterations: Users get 3 total drafts (1 initial + 2 refinements)

---

**Document Version:** 1.0  
**Last Updated:** 2024-02-27  
**API Version:** v1
