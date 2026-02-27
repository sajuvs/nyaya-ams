import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useRef, useEffect } from 'react'
import { gsap } from 'gsap'

interface Props {
  content: string
}

export default function MarkdownOutput({ content }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      gsap.fromTo(ref.current, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' })
    }
  }, [])

  return (
    <div
      ref={ref}
      className="border border-[#1a1a2e] glow-border-purple rounded-xl p-6 bg-[#0f0f1a] overflow-y-auto max-h-[70vh]"
    >
      <div className="prose prose-invert prose-sm max-w-none
        [&_h2]:text-[#00f5ff] [&_h2]:neon-cyan [&_h2]:tracking-wide [&_h2]:border-b [&_h2]:border-[#1a1a2e] [&_h2]:pb-2
        [&_h3]:text-[#bf00ff] [&_h3]:tracking-wide
        [&_strong]:text-[#e0e0ff]
        [&_table]:border-collapse [&_table]:w-full
        [&_th]:border [&_th]:border-[#1a1a2e] [&_th]:px-3 [&_th]:py-2 [&_th]:text-[#00f5ff] [&_th]:text-xs [&_th]:tracking-widest [&_th]:uppercase [&_th]:bg-[#0a0a0f]
        [&_td]:border [&_td]:border-[#1a1a2e] [&_td]:px-3 [&_td]:py-2 [&_td]:text-sm
        [&_blockquote]:border-l-2 [&_blockquote]:border-[#bf00ff] [&_blockquote]:pl-4 [&_blockquote]:text-[#4a4a6a] [&_blockquote]:italic
        [&_code]:bg-[#0a0a0f] [&_code]:text-[#00f5ff] [&_code]:px-1 [&_code]:rounded
        [&_hr]:border-[#1a1a2e]
        [&_li]:text-[#c0c0e0]
        [&_p]:text-[#c0c0e0]
      ">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>
    </div>
  )
}
