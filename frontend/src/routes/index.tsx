import { useRef, useState, useEffect, useCallback } from 'react'
import VoiceInput from '../components/VoiceInput'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { runAgent, type ResearchFindings } from '../api/agent'
import { AGENTS, type AgentStep } from '../utils/dummyData'
import AgentPipeline from '../components/AgentPipeline'
import AgentDetailPanel from '../components/AgentDetailPanel'
import MarkdownOutput from '../components/MarkdownOutput'
import FileUpload from '../components/FileUpload'

type Phase = 'input' | 'processing' | 'done'

export default function AgentPage() {
  const [phase, setPhase] = useState<Phase>('input')
  const [inputMode, setInputMode] = useState<'text' | 'voice'>('text')
  const [complaint, setComplaint] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [output, setOutput] = useState('')
  const [agentOutputs, setAgentOutputs] = useState<Record<string, ResearchFindings | string>>({})
  const [detailAgent, setDetailAgent] = useState<string | null>(null)

  const phaseRef = useRef<Phase>('input')
  const canViewResults = useRef(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const sec1Ref = useRef<HTMLDivElement>(null)
  const sec2Ref = useRef<HTMLDivElement>(null)
  const sec3Ref = useRef<HTMLDivElement>(null)
  const glitchRef = useRef<HTMLDivElement>(null)
  const hitlResolvers = useRef<Record<string, (approved: boolean) => void>>({})

  useEffect(() => { phaseRef.current = phase }, [phase])

  useEffect(() => {
    const block = (e: WheelEvent) => {
      const y = window.scrollY
      const vh = window.innerHeight
      const down = e.deltaY > 0
      if (y < vh * 0.9 && down && phaseRef.current === 'input') { e.preventDefault(); return }
      if (y >= vh * 0.9 && y < vh * 1.9 && down && !canViewResults.current) { e.preventDefault(); return }
    }
    const blockTouch = (e: TouchEvent) => {
      const y = window.scrollY
      const vh = window.innerHeight
      if (y < vh * 0.9 && phaseRef.current === 'input') { e.preventDefault(); return }
      if (y >= vh * 0.9 && y < vh * 1.9 && !canViewResults.current) { e.preventDefault(); return }
    }
    window.addEventListener('wheel', block, { passive: false })
    window.addEventListener('touchmove', blockTouch, { passive: false })
    return () => {
      window.removeEventListener('wheel', block)
      window.removeEventListener('touchmove', blockTouch)
    }
  }, [])

  const scrollTo = (section: HTMLDivElement | null, delay = 0) => {
    if (!section) return
    setTimeout(() => {
      gsap.to(window, { scrollTo: { y: section, offsetY: 0 }, duration: 2.2, ease: 'power4.inOut' })
    }, delay)
  }

  useGSAP(() => {
    gsap.set(sec2Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' })
    gsap.set(sec3Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' })

    const sections = [sec1Ref.current, sec2Ref.current, sec3Ref.current]
    sections.forEach((sec) => {
      if (!sec) return
      ScrollTrigger.create({
        trigger: sec,
        start: 'top top',
        end: '+=100%',
        pin: true,
        pinSpacing: false,
        anticipatePin: 1,
      })
    })

    gsap.timeline({
      scrollTrigger: { trigger: sec1Ref.current, start: 'top top', end: '+=600', scrub: 2.5 },
    })
      .to(sec1Ref.current, { yPercent: -8, scale: 0.92, opacity: 0, ease: 'power2.in' }, 0)
      .fromTo(
        sec1Ref.current?.querySelectorAll('.slice') ?? [],
        { y: 0, skewY: 0 },
        { y: (i) => (i % 2 === 0 ? -120 : 120), skewY: (i) => (i % 2 === 0 ? -4 : 4), stagger: 0.04, ease: 'power3.in' },
        0
      )

    gsap.timeline({
      scrollTrigger: { trigger: sec2Ref.current, start: 'top 90%', end: 'top top', scrub: 2 },
    })
      .fromTo(sec2Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' }, { scale: 1, opacity: 1, filter: 'blur(0px)', ease: 'power3.out' })

    gsap.timeline({
      scrollTrigger: { trigger: sec2Ref.current, start: 'top top', end: '+=600', scrub: 2.5 },
    })
      .to(sec2Ref.current, { scale: 1.12, opacity: 0, filter: 'blur(16px)', ease: 'power2.in' }, 0)

    gsap.timeline({
      scrollTrigger: { trigger: sec3Ref.current, start: 'top 90%', end: 'top top', scrub: 2 },
    })
      .fromTo(sec3Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' }, { scale: 1, opacity: 1, filter: 'blur(0px)', ease: 'power3.out' })

    return () => ScrollTrigger.getAll().forEach((t) => t.kill())
  }, { scope: containerRef })

  const waitForApproval = useCallback((agentId: string): Promise<boolean> => {
    return new Promise((resolve) => {
      hitlResolvers.current[agentId] = resolve
    })
  }, [])

  const handleApprove = (agentId: string) => {
    hitlResolvers.current[agentId]?.(true)
    delete hitlResolvers.current[agentId]
  }

  const handleReject = (agentId: string) => {
    hitlResolvers.current[agentId]?.(false)
    delete hitlResolvers.current[agentId]
  }

  const runPipeline = useCallback(async (complaintText: string, attachedFiles: File[]) => {
    const initialSteps: AgentStep[] = AGENTS.map((a, i) => ({
      agentId: a.id,
      status: i === 0 ? 'running' as const : 'pending' as const
    }))
    setSteps(initialSteps)
    scrollTo(sec2Ref.current, 400)

    try {
      const result = await runAgent(
        complaintText,
        attachedFiles,
        (agentId) => {
          setSteps((prev) => {
            const updated = prev.map((s) => s.agentId === agentId ? { ...s, status: 'done' as const } : s)
            const nextIdx = AGENTS.findIndex((a) => a.id === agentId) + 1
            const next = AGENTS[nextIdx]
            // Only auto-advance to running if the next agent doesn't require HITL
            if (next && !next.requiresApproval) {
              return updated.map((s) => s.agentId === next.id ? { ...s, status: 'running' as const } : s)
            }
            return updated
          })
        },
        async (agentId, output) => {
          setAgentOutputs((prev) => ({ ...prev, [agentId]: output }))
          setSteps((prev) => prev.map((s) =>
            s.agentId === agentId ? { ...s, status: 'awaiting-approval' as const } : s
          ))
          const approved = await waitForApproval(agentId)
          if (!approved) {
            setDetailAgent(null)
            setAgentOutputs((prev) => { const n = { ...prev }; delete n[agentId]; return n })
            setSteps((prev) => prev.map((s) => {
              if (s.agentId === agentId) return { ...s, status: 'pending' as const }
              if (s.agentId === 'document-drafter') return { ...s, status: 'running' as const }
              return s
            }))
          }
          return approved
        }
      )
      setOutput(result)
      setPhase('done')
    } catch (err) {
      console.error('Pipeline error:', err)
      // Reset stuck agents to show error state
      setSteps((prev) => prev.map((s) =>
        s.status === 'running' ? { ...s, status: 'pending' as const } : s
      ))
    }
  }, [waitForApproval])

  const handleSubmit = async () => {
    if (!complaint.trim()) return

    if (glitchRef.current) {
      gsap.timeline()
        .to(glitchRef.current, { opacity: 1, duration: 0.05 })
        .to(glitchRef.current, { opacity: 0, duration: 0.05 })
        .to(glitchRef.current, { opacity: 0.6, duration: 0.03 })
        .to(glitchRef.current, { opacity: 0, duration: 0.08 })
    }

    setPhase('processing')
    await runPipeline(complaint, files)
  }

  const handleReset = () => {
    // Hide sec2/sec3 immediately before scrolling so they're never visible during transition
    gsap.set(sec2Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' })
    gsap.set(sec3Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' })
    gsap.set(sec1Ref.current, { yPercent: 0, scale: 1, opacity: 1 })
    gsap.set(sec1Ref.current?.querySelectorAll('.slice') ?? [], { y: 0, skewY: 0 })
    window.scrollTo({ top: 0, behavior: 'instant' })
    setDetailAgent(null)
    canViewResults.current = false
    setPhase('input')
    setInputMode('text')
    setComplaint('')
    setFiles([])
    setSteps([])
    setOutput('')
    setAgentOutputs({})
  }

  return (
    <div ref={containerRef} className="relative" style={{ height: '300vh' }}>
      <div
        ref={glitchRef}
        className="pointer-events-none fixed inset-0 z-50 opacity-0"
        style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, #00f5ff08 2px, #00f5ff08 4px)' }}
      />
      <div className="pointer-events-none fixed top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-[#00f5ff06] blur-3xl" />
      <div className="pointer-events-none fixed bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full bg-[#bf00ff06] blur-3xl" />

      {/* ── SECTION 1: Input ── */}
      <section ref={sec1Ref} className="relative h-screen flex items-center justify-center overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="slice absolute inset-0 pointer-events-none" style={{
            background: `linear-gradient(135deg, #00f5ff0${i + 1}, #bf00ff0${i + 1})`,
            clipPath: `inset(${i * 16.66}% 0 ${100 - (i + 1) * 16.66}% 0)`,
            opacity: 0.03,
          }} />
        ))}
        <div className="relative z-10 w-full max-w-4xl px-8 flex flex-col items-center">
          <div className="mb-8 text-center w-full">
            {/* Mode toggle */}
            <div className="flex items-center justify-center mb-5">
              <div className="flex items-center gap-1.5 border border-[#1a1a2e] rounded-full p-1.5 bg-[#0a0a0f]">
                <button
                  onClick={() => setInputMode('voice')}
                  className={`flex items-center justify-center w-12 h-10 rounded-full text-sm font-medium transition-all duration-300 cursor-pointer ${
                    inputMode === 'voice'
                      ? 'bg-[#ff006e22] text-[#ff006e] border border-[#ff006e44] shadow-[0_0_16px_#ff006e22]'
                      : 'text-[#4a4a6a] hover:text-[#e0e0ff]'
                  }`}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="9" y="2" width="6" height="11" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/>
                  </svg>
                </button>
                <button
                  onClick={() => setInputMode('text')}
                  className={`flex items-center justify-center w-12 h-10 rounded-full text-sm font-medium transition-all duration-300 cursor-pointer ${
                    inputMode === 'text'
                      ? 'bg-[#00f5ff22] text-[#00f5ff] border border-[#00f5ff44] shadow-[0_0_16px_#00f5ff22]'
                      : 'text-[#4a4a6a] hover:text-[#e0e0ff]'
                  }`}
                >
                  <span style={{ fontFamily: 'Georgia, "Times New Roman", serif', fontSize: '15px', fontWeight: 700, letterSpacing: '-0.03em', lineHeight: 1 }}>Abc</span>
                </button>
              </div>
            </div>
            <p className="text-xs tracking-[0.4em] uppercase text-[#4a4a6a] mb-3">AI Legal Assessment</p>
            <h1 className="text-5xl font-bold text-[#e0e0ff] leading-tight mb-2">Know your rights.</h1>
            <p className="text-xl text-[#00f5ff] neon-cyan font-medium">Describe your situation.</p>
          </div>
          <div className="border border-[#1a1a2e] glow-border-cyan rounded-2xl p-8 bg-[#0f0f1a] w-full">
            <div style={{ height: '320px' }}>
              {inputMode === 'text' ? (
                <textarea
                  value={complaint}
                  onChange={(e) => setComplaint(e.target.value)}
                  placeholder="e.g. I paid ₹50,000 to a contractor for home renovation. He took the money but never started work and is now unreachable..."
                  className="w-full h-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-xl p-5 text-base text-[#e0e0ff] placeholder-[#2a2a4a] resize-none outline-none focus:border-[#00f5ff44] transition-colors duration-300"
                />
              ) : (
                <VoiceInput transcript={complaint} onTranscript={(text) => setComplaint(text)} />
              )}
            </div>

            <button
              onClick={handleSubmit}
              disabled={!complaint.trim()}
              className="mt-5 w-full py-4 rounded-xl text-sm tracking-[0.3em] uppercase font-medium transition-all duration-300
                bg-gradient-to-r from-[#00f5ff22] to-[#bf00ff22] border border-[#00f5ff44]
                text-[#00f5ff] hover:from-[#00f5ff33] hover:to-[#bf00ff33] hover:shadow-[0_0_30px_#00f5ff33]
                disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
            >
              Analyse →
            </button>
          </div>
        </div>
      </section>

      {/* ── SECTION 2: Pipeline ── */}
      <section ref={sec2Ref} className="relative h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'repeating-linear-gradient(90deg, transparent, transparent 80px, #00f5ff04 80px, #00f5ff04 81px)' }}
        />
        <div className="relative z-10 w-full h-full max-h-[90vh] flex items-center justify-center">
          <div className="flex flex-col items-center gap-6 w-full max-w-4xl px-8">
            <div className="text-center">
              <p className="text-xs tracking-[0.4em] uppercase text-[#4a4a6a] mb-2">Processing</p>
              <h2 className="text-3xl font-bold text-[#e0e0ff]">Agent Pipeline</h2>
              <p className="text-base text-[#4a4a6a] mt-1">Sequential analysis in progress</p>
            </div>
            <AgentPipeline
              steps={steps}
              onApprove={handleApprove}
              onReject={handleReject}
              agentOutputs={agentOutputs}
              onToggleDetail={(agentId) => {
                setDetailAgent(detailAgent === agentId ? null : agentId)
              }}
            />
            {phase === 'done' && (
              <button
                onClick={() => { canViewResults.current = true; scrollTo(sec3Ref.current, 600) }}
                className="text-xs tracking-[0.3em] uppercase text-[#00f5ff] border border-[#00f5ff44] px-8 py-3 rounded-lg
                  hover:bg-[#00f5ff11] transition-all cursor-pointer animate-pulse"
              >
                View Results ↓
              </button>
            )}
          </div>
        </div>
      </section>

      <AgentDetailPanel
        isOpen={detailAgent !== null && !!agentOutputs[detailAgent ?? '']}
        agentName={detailAgent ? (AGENTS.find((a) => a.id === detailAgent)?.name ?? '') : ''}
        data={detailAgent ? (agentOutputs[detailAgent] ?? null) : null}
        onClose={() => setDetailAgent(null)}
      />

      {/* ── SECTION 3: Output ── */}
      <section ref={sec3Ref} className="relative h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse at center, #bf00ff08 0%, transparent 70%)' }}
        />
        <div className="relative z-10 w-full max-w-5xl px-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-xs tracking-[0.4em] uppercase text-[#4a4a6a]">Assessment Complete</p>
              <h2 className="text-2xl font-bold text-[#e0e0ff] mt-0.5">Legal Analysis</h2>
            </div>
            <button
              onClick={handleReset}
              className="text-xs tracking-widest uppercase text-[#4a4a6a] hover:text-[#00f5ff] transition-colors cursor-pointer border border-[#1a1a2e] px-4 py-2 rounded-lg hover:border-[#00f5ff44]"
            >
              ← New Query
            </button>
          </div>
          {output && <MarkdownOutput content={output} />}
        </div>
      </section>

    </div>
  )
}
