import { useRef, useEffect } from 'react'
import { gsap } from 'gsap'
import type { AgentStep } from '../utils/dummyData'
import { AGENTS } from '../utils/dummyData'

interface Props {
  steps: AgentStep[]
}

export default function AgentPipeline({ steps }: Props) {
  const itemRefs = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    steps.forEach((step, i) => {
      const el = itemRefs.current[i]
      if (!el) return
      if (step.status === 'running') {
        gsap.to(el, { borderColor: '#00f5ff', boxShadow: '0 0 20px #00f5ff44', duration: 0.3 })
      } else if (step.status === 'done') {
        gsap.to(el, { borderColor: '#bf00ff', boxShadow: '0 0 12px #bf00ff33', duration: 0.4 })
      }
    })
  }, [steps])

  return (
    <div className="flex flex-col gap-3 w-full max-w-sm">
      {AGENTS.map((agent, i) => {
        const step = steps.find((s) => s.agentId === agent.id)
        const status = step?.status ?? 'pending'

        return (
          <div
            key={agent.id}
            ref={(el) => { itemRefs.current[i] = el }}
            className="border border-[#1a1a2e] rounded-lg p-4 bg-[#0f0f1a] transition-all duration-300"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs tracking-widest uppercase text-[#4a4a6a]">
                Agent {String(i + 1).padStart(2, '0')}
              </span>
              <StatusBadge status={status} />
            </div>
            <p className="text-sm text-[#e0e0ff] font-medium">{agent.name}</p>
            <p className="text-xs text-[#4a4a6a] mt-0.5">{agent.role}</p>
            {status === 'running' && (
              <div className="mt-2 flex gap-1">
                {[0, 1, 2].map((d) => (
                  <span
                    key={d}
                    className="w-1 h-1 rounded-full bg-[#00f5ff] animate-bounce"
                    style={{ animationDelay: `${d * 0.15}s` }}
                  />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function StatusBadge({ status }: { status: AgentStep['status'] | 'pending' }) {
  const map = {
    pending: { label: 'Waiting', color: 'text-[#4a4a6a]' },
    running: { label: 'Running', color: 'text-[#00f5ff]' },
    done: { label: 'Done', color: 'text-[#bf00ff]' },
  }
  const { label, color } = map[status]
  return <span className={`text-xs tracking-wider ${color}`}>{label}</span>
}
