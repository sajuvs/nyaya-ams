import { useRef, useState, useEffect, useCallback } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { runAgent } from '../api/agent'
import { AGENTS, type AgentStep } from '../utils/dummyData'
import AgentPipeline from '../components/AgentPipeline'
import MarkdownOutput from '../components/MarkdownOutput'
import FileUpload from '../components/FileUpload'

type Phase = 'input' | 'processing' | 'done'

export default function AgentPage() {
  const [phase, setPhase] = useState<Phase>('input')
  const [complaint, setComplaint] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [output, setOutput] = useState('')

  const phaseRef = useRef<Phase>('input')
  const containerRef = useRef<HTMLDivElement>(null)
  const sec1Ref = useRef<HTMLDivElement>(null)
  const sec2Ref = useRef<HTMLDivElement>(null)
  const sec3Ref = useRef<HTMLDivElement>(null)
  const glitchRef = useRef<HTMLDivElement>(null)
  // Holds resolve functions for HITL pauses keyed by agentId
  const hitlResolvers = useRef<Record<string, (approved: boolean) => void>>({})

  // Keep phaseRef in sync for use inside event listeners
  useEffect(() => { phaseRef.current = phase }, [phase])

  // Block scroll forward when phase hasn't unlocked the next section
  useEffect(() => {
    const block = (e: Event) => {
      const y = window.scrollY
      const vh = window.innerHeight
      const isScrollingDown = e instanceof WheelEvent ? e.deltaY > 0 : true
      if (!isScrollingDown) return
      if (y < vh * 0.5 && phaseRef.current === 'input') e.preventDefault()
      else if (y >= vh * 0.5 && y < vh * 1.5 && phaseRef.current === 'processing') e.preventDefault()
    }
    window.addEventListener('wheel', block, { passive: false })
    window.addEventListener('touchmove', block, { passive: false })
    return () => {
      window.removeEventListener('wheel', block)
      window.removeEventListener('touchmove', block)
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

    // Sec 1 exit: shatter slices
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

    // Sec 2 entrance: zoom through from small
    gsap.timeline({
      scrollTrigger: { trigger: sec2Ref.current, start: 'top 90%', end: 'top top', scrub: 2 },
    })
      .fromTo(sec2Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' }, { scale: 1, opacity: 1, filter: 'blur(0px)', ease: 'power3.out' })

    // Sec 2 exit: zoom past camera
    gsap.timeline({
      scrollTrigger: { trigger: sec2Ref.current, start: 'top top', end: '+=600', scrub: 2.5 },
    })
      .to(sec2Ref.current, { scale: 1.12, opacity: 0, filter: 'blur(16px)', ease: 'power2.in' }, 0)

    // Sec 3 entrance: zoom through from small
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

    const result = await runAgent(
      complaintText,
      attachedFiles,
      (agentId) => {
        setSteps((prev) => {
          const updated = prev.map((s) => s.agentId === agentId ? { ...s, status: 'done' as const } : s)
          const next = AGENTS[AGENTS.findIndex((a) => a.id === agentId) + 1]
          if (next) return updated.map((s) => s.agentId === next.id ? { ...s, status: 'running' as const } : s)
          return updated
        })
      },
      async (agentId) => {
        // Pause and show HITL UI
        setSteps((prev) => prev.map((s) => s.agentId === agentId ? { ...s, status: 'awaiting-approval' as const } : s))
        const approved = await waitForApproval(agentId)
        if (!approved) {
          // Re-run: reset this agent and all subsequent to pending, then re-run
          setSteps((prev) => prev.map((s) => {
            const idx = AGENTS.findIndex((a) => a.id === s.agentId)
            const thisIdx = AGENTS.findIndex((a) => a.id === agentId)
            return idx >= thisIdx ? { ...s, status: 'pending' as const } : s
          }))
          // Small delay so user sees the reset
          await new Promise((r) => setTimeout(r, 600))
          setSteps((prev) => prev.map((s) => s.agentId === agentId ? { ...s, status: 'running' as const } : s))
        }
        return approved
      }
    )

    setOutput(result)
    setPhase('done')
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
    setPhase('input')
    setComplaint('')
    setFiles([])
    setSteps([])
    setOutput('')
    gsap.set(sec2Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' })
    gsap.set(sec3Ref.current, { scale: 0.82, opacity: 0, filter: 'blur(20px)' })
    gsap.set(sec1Ref.current, { yPercent: 0, scale: 1, opacity: 1 })
    gsap.set(sec1Ref.current?.querySelectorAll('.slice') ?? [], { y: 0, skewY: 0 })
    scrollTo(sec1Ref.current)
  }

  const displaySteps = steps

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
        <div className="relative z-10 w-full max-w-2xl px-6 flex flex-col items-center">
          <div className="mb-8 text-center w-full">
            <p className="text-xs tracking-[0.4em] uppercase text-[#4a4a6a] mb-3">AI Legal Assessment</p>
            <h1 className="text-4xl font-bold text-[#e0e0ff] leading-tight mb-2">Know your rights.</h1>
            <p className="text-lg text-[#00f5ff] neon-cyan font-medium">Describe your situation.</p>
          </div>
          <div className="border border-[#1a1a2e] glow-border-cyan rounded-2xl p-6 bg-[#0f0f1a] w-full">
            <textarea
              value={complaint}
              onChange={(e) => setComplaint(e.target.value)}
              placeholder="e.g. I paid ₹50,000 to a contractor for home renovation. He took the money but never started work and is now unreachable..."
              rows={9}
              className="w-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-xl p-4 text-sm text-[#e0e0ff] placeholder-[#2a2a4a] resize-none outline-none focus:border-[#00f5ff44] transition-colors duration-300"
            />

            <button
              onClick={handleSubmit}
              disabled={!complaint.trim()}
              className="mt-4 w-full py-3 rounded-xl text-sm tracking-[0.3em] uppercase font-medium transition-all duration-300
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
        <div className="relative z-10 flex flex-col items-center gap-8 px-6 w-full max-w-lg">
          <div className="text-center">
            <p className="text-xs tracking-[0.4em] uppercase text-[#4a4a6a] mb-2">Processing</p>
            <h2 className="text-2xl font-bold text-[#e0e0ff]">Agent Pipeline</h2>
            <p className="text-sm text-[#4a4a6a] mt-1">Sequential analysis in progress</p>
          </div>
          <AgentPipeline steps={displaySteps} onApprove={handleApprove} onReject={handleReject} />
          {phase === 'done' && (
            <button
              onClick={() => scrollTo(sec3Ref.current, 600)}
              className="text-xs tracking-[0.3em] uppercase text-[#00f5ff] border border-[#00f5ff44] px-6 py-2 rounded-lg
                hover:bg-[#00f5ff11] transition-all cursor-pointer animate-pulse"
            >
              View Results ↓
            </button>
          )}
        </div>
      </section>

      {/* ── SECTION 3: Output ── */}
      <section ref={sec3Ref} className="relative h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse at center, #bf00ff08 0%, transparent 70%)' }}
        />
        <div className="relative z-10 w-full max-w-3xl px-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <p className="text-xs tracking-[0.4em] uppercase text-[#4a4a6a]">Assessment Complete</p>
              <h2 className="text-xl font-bold text-[#e0e0ff] mt-0.5">Legal Analysis</h2>
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
