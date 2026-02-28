import { useRef, useEffect } from 'react'
import gsap from 'gsap'
import type { AgentStep } from '../utils/dummyData'
import { AGENTS } from '../utils/dummyData'

interface Props {
  steps: AgentStep[]
  onApprove: (agentId: string) => void
  onReject: (agentId: string) => void
}

export default function AgentPipeline({ steps, onApprove, onReject }: Props) {
  const itemRefs = useRef<(HTMLDivElement | null)[]>([])
  const prevStatuses = useRef<string[]>([])

  useEffect(() => {
    steps.forEach((step, i) => {
      const el = itemRefs.current[i]
      if (!el) return
      const prev = prevStatuses.current[i]
      if (prev === step.status) return

      if (step.status === 'running') {
        gsap.to(el, { borderColor: '#00f5ff', boxShadow: '0 0 24px #00f5ff55', duration: 0.4 })
        gsap.to(el, { height: 'auto', duration: 0.5, ease: 'power3.out' })
      } else if (step.status === 'awaiting-approval') {
        gsap.to(el, { borderColor: '#ff006e', boxShadow: '0 0 24px #ff006e44', duration: 0.4 })
      } else if (step.status === 'done') {
        gsap.to(el, { borderColor: '#bf00ff', boxShadow: '0 0 12px #bf00ff33', duration: 0.4 })
      } else {
        gsap.to(el, { borderColor: '#1a1a2e', boxShadow: 'none', duration: 0.3 })
      }

      prevStatuses.current[i] = step.status
    })
  }, [steps])

  return (
    <div className="flex flex-col gap-3 w-full max-w-lg">
      {AGENTS.map((agent, i) => {
        const step = steps.find((s) => s.agentId === agent.id)
        const status = step?.status ?? 'pending'
        const isActive = status === 'running' || status === 'awaiting-approval'

        return (
          <div
            key={agent.id}
            ref={(el) => { itemRefs.current[i] = el }}
            className="border border-[#1a1a2e] rounded-xl bg-[#0f0f1a] overflow-hidden transition-all duration-500"
            style={{ padding: isActive ? '1.5rem' : '1rem' }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-1.5 rounded-full transition-all duration-500 ${
                  isActive ? 'h-8 bg-[#00f5ff]' : status === 'done' ? 'h-4 bg-[#bf00ff]' : 'h-4 bg-[#1a1a2e]'
                }`} />
                <div>
                  <span className="text-xs tracking-widest uppercase text-[#4a4a6a]">
                    Agent {String(i + 1).padStart(2, '0')}
                    {agent.requiresApproval && (
                      <span className="ml-2 text-[#ff006e]">· HITL</span>
                    )}
                  </span>
                  <p className={`font-semibold transition-all duration-300 ${
                    isActive ? 'text-base text-[#e0e0ff]' : 'text-sm text-[#a0a0c0]'
                  }`}>{agent.name}</p>
                </div>
              </div>
              <StatusBadge status={status} />
            </div>

            {/* Expanded content when active */}
            {isActive && (
              <div className="mt-4 pl-4 border-l border-[#1a1a2e]">
                {status === 'running' && (
                  <>
                    <p className="text-sm text-[#4a4a6a] leading-relaxed">{agent.runningDescription}</p>
                    <div className="mt-3 flex gap-1.5 items-center">
                      {[0, 1, 2, 3, 4].map((d) => (
                        <span
                          key={d}
                          className="w-1 h-1 rounded-full bg-[#00f5ff] animate-bounce"
                          style={{ animationDelay: `${d * 0.12}s` }}
                        />
                      ))}
                      <span className="text-xs text-[#00f5ff] ml-2 tracking-widest">Processing</span>
                    </div>
                  </>
                )}

                {status === 'awaiting-approval' && (
                  <>
                    <p className="text-sm text-[#c0c0e0] leading-relaxed mb-4">
                      {agent.id === 'legal-researcher'
                        ? 'Research complete. Review the findings before the Document Drafter proceeds.'
                        : 'Assessment complete. Approve to generate the final output.'}
                    </p>
                    <div className="flex gap-3">
                      <button
                        onClick={() => onApprove(agent.id)}
                        className="flex-1 py-2 rounded-lg text-xs tracking-widest uppercase border border-[#00f5ff44]
                          text-[#00f5ff] hover:bg-[#00f5ff11] transition-all cursor-pointer"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => onReject(agent.id)}
                        className="flex-1 py-2 rounded-lg text-xs tracking-widest uppercase border border-[#ff006e44]
                          text-[#ff006e] hover:bg-[#ff006e11] transition-all cursor-pointer"
                      >
                        ✕ Re-run
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Collapsed done state */}
            {status === 'done' && (
              <p className="text-xs text-[#4a4a6a] mt-1 pl-[1.125rem]">{agent.role}</p>
            )}
          </div>
        )
      })}
    </div>
  )
}

function StatusBadge({ status }: { status: AgentStep['status'] | 'pending' }) {
  const map: Record<string, { label: string; color: string }> = {
    pending: { label: 'Waiting', color: 'text-[#4a4a6a]' },
    running: { label: 'Running', color: 'text-[#00f5ff]' },
    'awaiting-approval': { label: 'Review', color: 'text-[#ff006e]' },
    done: { label: 'Done', color: 'text-[#bf00ff]' },
  }
  const { label, color } = map[status] ?? map.pending
  return <span className={`text-xs tracking-wider ${color}`}>{label}</span>
}
