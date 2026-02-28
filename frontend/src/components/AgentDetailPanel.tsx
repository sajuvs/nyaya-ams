import { useRef, useEffect } from 'react'
import gsap from 'gsap'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ResearchFindings } from '../api/agent'

interface Props {
  isOpen: boolean
  agentName: string
  data: ResearchFindings | string | null
  onClose: () => void
}

export default function AgentDetailPanel({ isOpen, agentName, data, onClose }: Props) {
  const drawerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!drawerRef.current) return
    if (isOpen) {
      gsap.fromTo(drawerRef.current,
        { x: '100%', opacity: 0 },
        { x: '0%', opacity: 1, duration: 0.45, ease: 'power3.out' }
      )
    } else {
      gsap.to(drawerRef.current, { x: '100%', opacity: 0, duration: 0.35, ease: 'power3.in' })
    }
  }, [isOpen])

  const isResearch = data !== null && typeof data === 'object'

  return (
    <div
      ref={drawerRef}
      className="fixed top-0 right-0 h-full w-[380px] z-40 flex flex-col border-l border-[#1a1a2e] bg-[#0a0a0f]"
      style={{ transform: 'translateX(100%)', opacity: 0, boxShadow: '-8px 0 40px rgba(0,0,0,0.6)' }}
    >
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#1a1a2e] shrink-0">
        <div>
          <p className="text-xs tracking-[0.3em] uppercase text-[#4a4a6a]">Agent Output</p>
          <h3 className="text-sm font-semibold text-[#e0e0ff]">{agentName}</h3>
        </div>
        <button onClick={onClose} className="text-[#4a4a6a] hover:text-[#ff006e] transition-colors cursor-pointer text-xl leading-none">×</button>
      </div>

      <div
        className="overflow-y-auto px-5 py-4 flex flex-col gap-4 flex-1"
        onWheel={(e) => e.stopPropagation()}
        onTouchMove={(e) => e.stopPropagation()}
      >
        {data && (isResearch ? (
          <ResearchView data={data as ResearchFindings} />
        ) : (
          <DraftView content={data as string} />
        ))}
      </div>
    </div>
  )
}

function ResearchView({ data }: { data: ResearchFindings }) {
  const facts = Array.isArray(data.summary_of_facts) ? data.summary_of_facts : []
  const provisions = Array.isArray(data.legal_provisions) ? data.legal_provisions : []
  const score = Number(data.merits_score) || 0

  return (
    <>
      <div className="flex items-center gap-4">
        <div className="text-center">
          <p className="text-3xl font-bold text-[#00f5ff] neon-cyan">{score}<span className="text-sm text-[#4a4a6a]">/10</span></p>
          <p className="text-xs tracking-widest uppercase text-[#4a4a6a] mt-0.5">Case Strength</p>
        </div>
        <div className="flex-1 h-px bg-gradient-to-r from-[#00f5ff44] to-transparent" />
      </div>

      {facts.length > 0 && (
        <Section title="Key Facts">
          <ul className="flex flex-col gap-1.5">
            {facts.map((f, i) => (
              <li key={i} className="flex gap-2 text-sm text-[#c0c0e0]">
                <span className="text-[#00f5ff] shrink-0">·</span>{f}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {provisions.length > 0 && (
        <Section title="Applicable Laws">
          <ul className="flex flex-col gap-1.5">
            {provisions.map((p, i) => (
              <li key={i} className="flex gap-2 text-sm text-[#c0c0e0]">
                <span className="text-[#bf00ff] shrink-0">§</span>{p}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {data.kerala_specific && (
        <Section title="Kerala Jurisdiction">
          <p className="text-sm text-[#c0c0e0] leading-relaxed">{data.kerala_specific}</p>
        </Section>
      )}
    </>
  )
}

function DraftView({ content }: { content: string }) {
  return (
    <div className="prose prose-invert prose-sm max-w-none
      [&_h2]:text-[#00f5ff] [&_h3]:text-[#bf00ff]
      [&_strong]:text-[#e0e0ff]
      [&_table]:border-collapse [&_th]:border [&_th]:border-[#1a1a2e] [&_th]:px-3 [&_th]:py-2 [&_th]:text-[#00f5ff] [&_th]:text-xs [&_th]:bg-[#0a0a0f]
      [&_td]:border [&_td]:border-[#1a1a2e] [&_td]:px-3 [&_td]:py-2 [&_td]:text-sm
      [&_blockquote]:border-l-2 [&_blockquote]:border-[#bf00ff] [&_blockquote]:pl-4 [&_blockquote]:text-[#4a4a6a]
      [&_code]:bg-[#0a0a0f] [&_code]:text-[#00f5ff] [&_code]:px-1 [&_code]:rounded
      [&_hr]:border-[#1a1a2e] [&_li]:text-[#c0c0e0] [&_p]:text-[#c0c0e0]">
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs tracking-[0.3em] uppercase text-[#4a4a6a] mb-2">{title}</p>
      {children}
    </div>
  )
}
