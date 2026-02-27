import { useEffect, useRef, useState } from 'react'
import { gsap } from 'gsap'
import { getAgents, updateAgentPrompt } from '../api/agent'
import type { Agent } from '../utils/dummyData'

export default function PromptsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selected, setSelected] = useState<Agent | null>(null)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getAgents().then(setAgents)
  }, [])

  useEffect(() => {
    if (listRef.current) {
      gsap.fromTo(
        listRef.current.children,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, stagger: 0.08, duration: 0.4, ease: 'power2.out' }
      )
    }
  }, [agents])

  const openModal = (agent: Agent) => {
    setSelected(agent)
    setDraft(agent.systemPrompt)
    setSaved(false)
    requestAnimationFrame(() => {
      if (modalRef.current) {
        gsap.fromTo(modalRef.current, { opacity: 0, scale: 0.95 }, { opacity: 1, scale: 1, duration: 0.25, ease: 'power2.out' })
      }
    })
  }

  const closeModal = () => {
    if (modalRef.current) {
      gsap.to(modalRef.current, {
        opacity: 0, scale: 0.95, duration: 0.2, ease: 'power2.in',
        onComplete: () => setSelected(null),
      })
    } else {
      setSelected(null)
    }
  }

  const handleSave = async () => {
    if (!selected) return
    setSaving(true)
    await updateAgentPrompt(selected.id, draft)
    setAgents((prev) => prev.map((a) => a.id === selected.id ? { ...a, systemPrompt: draft } : a))
    setSelected((prev) => prev ? { ...prev, systemPrompt: draft } : prev)
    setSaving(false)
    setSaved(true)
  }

  return (
    <div className="max-w-4xl mx-auto px-8 py-12">
      <div className="mb-8">
        <p className="text-xs tracking-widest uppercase text-[#4a4a6a] mb-1">Nyaya-flow / Configuration</p>
        <h1 className="text-2xl font-bold text-[#e0e0ff]">System Prompts</h1>
        <p className="text-sm text-[#4a4a6a] mt-1">Configure the behaviour of each agent in the pipeline.</p>
      </div>

      <div ref={listRef} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {agents.map((agent, i) => (
          <div
            key={agent.id}
            onClick={() => openModal(agent)}
            className="border border-[#1a1a2e] rounded-xl p-5 bg-[#0f0f1a] cursor-pointer
              hover:border-[#00f5ff44] hover:shadow-[0_0_16px_#00f5ff11] transition-all duration-300 group"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs tracking-widest uppercase text-[#4a4a6a]">Agent {String(i + 1).padStart(2, '0')}</span>
                <h3 className="text-base font-semibold text-[#e0e0ff] mt-1 group-hover:text-[#00f5ff] transition-colors">{agent.name}</h3>
                <p className="text-xs text-[#4a4a6a] mt-0.5">{agent.role}</p>
              </div>
              <span className="text-[#1a1a2e] group-hover:text-[#00f5ff] text-lg transition-colors">→</span>
            </div>
            <p className="text-xs text-[#2a2a4a] mt-3 line-clamp-2 font-mono leading-relaxed">
              {agent.systemPrompt.slice(0, 100)}…
            </p>
          </div>
        ))}
      </div>

      {/* Modal */}
      {selected && (
        <div
          className="fixed inset-0 bg-[#0a0a0f99] backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={(e) => { if (e.target === e.currentTarget) closeModal() }}
        >
          <div
            ref={modalRef}
            className="w-full max-w-2xl border border-[#1a1a2e] glow-border-cyan rounded-2xl bg-[#0f0f1a] p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-xs tracking-widest uppercase text-[#4a4a6a]">{selected.name}</p>
                <p className="text-sm text-[#4a4a6a]">{selected.role}</p>
              </div>
              <button onClick={closeModal} className="text-[#4a4a6a] hover:text-[#ff006e] text-xl transition-colors cursor-pointer">×</button>
            </div>

            <textarea
              value={draft}
              onChange={(e) => { setDraft(e.target.value); setSaved(false) }}
              rows={14}
              className="w-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-xl p-4 text-sm text-[#e0e0ff] font-mono resize-none outline-none focus:border-[#00f5ff44] transition-colors duration-300 leading-relaxed"
            />

            <div className="flex items-center justify-between mt-4">
              <span className="text-xs text-[#4a4a6a]">
                {draft.length} chars
              </span>
              <div className="flex gap-3">
                <button onClick={closeModal} className="px-4 py-2 text-xs tracking-widest uppercase text-[#4a4a6a] hover:text-[#e0e0ff] transition-colors cursor-pointer">
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-5 py-2 text-xs tracking-widest uppercase rounded-lg border border-[#00f5ff44] text-[#00f5ff]
                    hover:bg-[#00f5ff11] transition-all duration-300 disabled:opacity-50 cursor-pointer"
                >
                  {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
