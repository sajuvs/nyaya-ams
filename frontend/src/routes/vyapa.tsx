import { useState, useRef, useCallback } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { runAgent } from '../api/agent'

type Phase = 'input' | 'processing' | 'done'
type AgentStatus = 'pending' | 'running' | 'done'

const AGENTS = [
  { id: 'researcher', label: 'Researcher', desc: 'Scouring specs, reviews, pricing and known issues across the web…' },
  { id: 'drafter',    label: 'Drafter',    desc: 'Structuring findings into a clear side-by-side comparison…' },
  { id: 'reviewer',   label: 'Reviewer',   desc: 'Auditing the comparison for accuracy, balance and completeness…' },
]

export default function VyapaPage() {
  const [phase, setPhase] = useState<Phase>('input')
  const [productA, setProductA] = useState('')
  const [productB, setProductB] = useState('')
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({})
  const [output, setOutput] = useState('')
  const queryRef = useRef<{ a: string; b: string }>({ a: '', b: '' })

  const setStatus = (id: string, status: AgentStatus) =>
    setAgentStatuses((prev) => ({ ...prev, [id]: status }))

  const handleSubmit = useCallback(async () => {
    if (!productA.trim() || !productB.trim()) return
    queryRef.current = { a: productA, b: productB }

    const initial: Record<string, AgentStatus> = { researcher: 'running', drafter: 'pending', reviewer: 'pending' }
    setAgentStatuses(initial)
    setPhase('processing')

    const grievance = `Compare these two products: Product A: ${productA} | Product B: ${productB}. Provide a detailed comparison including specs, pricing, pros/cons, known issues, and a clear recommendation.`

    try {
      const result = await runAgent(
        grievance, [],
        (agentId) => {
          const map: Record<string, string> = {
            'legal-researcher': 'researcher',
            'document-drafter': 'drafter',
            'viability-assessor': 'reviewer',
          }
          const vid = map[agentId]
          if (vid) setStatus(vid, 'done')
        },
        undefined,
        'product_comparison',
        (agentId) => {
          const map: Record<string, string> = {
            'legal-researcher': 'researcher',
            'document-drafter': 'drafter',
            'viability-assessor': 'reviewer',
          }
          const vid = map[agentId]
          if (vid) setStatus(vid, 'running')
        }
      )
      setStatus('reviewer', 'done')
      setOutput(result)
      setPhase('done')
    } catch (err) {
      console.error(err)
      setPhase('input')
    }
  }, [productA, productB])

  const handleReset = () => {
    setPhase('input')
    setProductA('')
    setProductB('')
    setAgentStatuses({})
    setOutput('')
  }

  return (
    <div className="h-screen bg-white flex flex-col overflow-hidden">

      {/* ── Input phase ── */}
      {phase === 'input' && (
        <div className="flex-1 flex flex-col items-center justify-center px-6 py-16">
          <p className="text-xs tracking-[0.4em] uppercase text-gray-400 mb-2">Product Intelligence</p>
          <h1 className="text-5xl font-bold text-gray-900 mb-2 tracking-tight">Compare anything.</h1>
          <p className="text-lg text-gray-400 mb-12">Enter two products, URLs, or search queries.</p>

          <div className="w-full max-w-2xl flex flex-col gap-4">
            <div className="flex gap-3">
              <div className="flex-1 flex flex-col gap-1">
                <label className="text-xs tracking-widest uppercase text-gray-400 pl-1">Product A</label>
                <input
                  value={productA}
                  onChange={(e) => setProductA(e.target.value)}
                  placeholder="e.g. iPhone 15 Pro or paste a URL"
                  className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-900 placeholder-gray-300 outline-none focus:border-gray-400 transition-colors bg-white"
                />
              </div>
              <div className="flex items-end pb-0.5">
                <span className="text-gray-300 text-2xl font-light pb-3">vs</span>
              </div>
              <div className="flex-1 flex flex-col gap-1">
                <label className="text-xs tracking-widest uppercase text-gray-400 pl-1">Product B</label>
                <input
                  value={productB}
                  onChange={(e) => setProductB(e.target.value)}
                  placeholder="e.g. Samsung S24 Ultra or paste a URL"
                  className="w-full border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-900 placeholder-gray-300 outline-none focus:border-gray-400 transition-colors bg-white"
                />
              </div>
            </div>

            <button
              onClick={handleSubmit}
              disabled={!productA.trim() || !productB.trim()}
              className="w-full py-3.5 rounded-xl text-sm tracking-[0.2em] uppercase font-medium bg-gray-900 text-white
                hover:bg-gray-700 transition-colors disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
            >
              Compare →
            </button>
          </div>
        </div>
      )}

      {/* ── Processing + Done phase ── */}
      {(phase === 'processing' || phase === 'done') && (
        <div className="flex-1 flex flex-col items-center px-6 py-12 gap-8 overflow-y-auto">

          {/* Sticky query pill */}
          <div className="flex items-center gap-3 border border-gray-200 rounded-full px-5 py-2 bg-gray-50 text-sm text-gray-600">
            <span className="font-medium text-gray-900">{queryRef.current.a}</span>
            <span className="text-gray-300">vs</span>
            <span className="font-medium text-gray-900">{queryRef.current.b}</span>
            {phase === 'done' && (
              <button onClick={handleReset} className="ml-3 text-xs tracking-widest uppercase text-gray-400 hover:text-gray-700 transition-colors cursor-pointer border-l border-gray-200 pl-3">
                New
              </button>
            )}
          </div>

          {/* Agent stepper */}
          <div className="w-full max-w-2xl flex items-start gap-0">
            {AGENTS.map((agent, i) => {
              const status = agentStatuses[agent.id] ?? 'pending'
              return (
                <div key={agent.id} className="flex items-start flex-1">
                  <div className="flex flex-col items-center flex-1">
                    {/* Circle */}
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
                      status === 'done'    ? 'bg-gray-900 border-gray-900' :
                      status === 'running' ? 'bg-white border-gray-900' :
                                            'bg-white border-gray-200'
                    }`}>
                      {status === 'done' ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                      ) : status === 'running' ? (
                        <div className="flex gap-0.5">
                          {[0,1,2].map((d) => (
                            <span key={d} className="w-1 h-1 rounded-full bg-gray-900 animate-bounce" style={{ animationDelay: `${d * 0.15}s` }} />
                          ))}
                        </div>
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-gray-200" />
                      )}
                    </div>
                    <p className={`text-xs mt-2 tracking-widest uppercase transition-colors duration-300 ${
                      status === 'pending' ? 'text-gray-300' : 'text-gray-700'
                    }`}>{agent.label}</p>
                  </div>
                  {/* Connector line — aligned to circle centre (top 20px = half of 40px circle) */}
                  {i < AGENTS.length - 1 && (
                    <div className="flex-none w-8 mt-5">
                      <div className={`h-px transition-colors duration-500 ${
                        (agentStatuses[AGENTS[i+1].id] ?? 'pending') !== 'pending' ? 'bg-gray-900' : 'bg-gray-200'
                      }`} />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Output */}
          {phase === 'done' && output && (
            <div className="w-full max-w-3xl border border-gray-200 rounded-2xl p-8 bg-white">
              <div className="prose prose-gray max-w-none
                [&_h1]:text-gray-900 [&_h1]:font-bold [&_h1]:text-2xl
                [&_h2]:text-gray-800 [&_h2]:font-semibold [&_h2]:text-lg [&_h2]:border-b [&_h2]:border-gray-100 [&_h2]:pb-2
                [&_h3]:text-gray-700 [&_h3]:font-medium
                [&_strong]:text-gray-900
                [&_table]:w-full [&_table]:border-collapse
                [&_th]:border [&_th]:border-gray-200 [&_th]:px-4 [&_th]:py-2.5 [&_th]:text-xs [&_th]:tracking-widest [&_th]:uppercase [&_th]:text-gray-500 [&_th]:bg-gray-50
                [&_td]:border [&_td]:border-gray-100 [&_td]:px-4 [&_td]:py-2.5 [&_td]:text-sm [&_td]:text-gray-700
                [&_tr:hover_td]:bg-gray-50
                [&_blockquote]:border-l-4 [&_blockquote]:border-gray-200 [&_blockquote]:pl-4 [&_blockquote]:text-gray-500 [&_blockquote]:italic
                [&_code]:bg-gray-100 [&_code]:text-gray-700 [&_code]:px-1.5 [&_code]:rounded [&_code]:text-sm
                [&_hr]:border-gray-100
                [&_li]:text-gray-700
                [&_p]:text-gray-700 [&_p]:leading-relaxed
                [&_ul]:space-y-1 [&_ol]:space-y-1
              ">
                <Markdown remarkPlugins={[remarkGfm]}>{output}</Markdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
