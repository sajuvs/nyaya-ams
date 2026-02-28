import { useState, useRef, useEffect, useCallback } from 'react'
import gsap from 'gsap'

type RecordState = 'idle' | 'recording' | 'transcribing'

interface Props {
  onTranscript: (text: string) => void
  transcript: string
}

async function transcribeAudio(_blob: Blob): Promise<string> {
  // TODO: integrate transcription service here
  await new Promise((r) => setTimeout(r, 1500))
  return ''
}

const BARS = 48
const INNER_R = 52
const OUTER_MAX = 36

export default function VoiceInput({ onTranscript, transcript }: Props) {
  const [state, setState] = useState<RecordState>('idle')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number>(0)
  const transcriptBoxRef = useRef<HTMLDivElement>(null)
  const idleAnimRef = useRef<number>(0)
  const idlePhaseRef = useRef(0)

  const isRecording = state === 'recording'
  const isTranscribing = state === 'transcribing'

  useEffect(() => {
    if (transcriptBoxRef.current) {
      gsap.fromTo(transcriptBoxRef.current,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }
      )
    }
  }, [])

  // Idle breathing animation on canvas
  const drawIdle = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const cx = canvas.width / 2, cy = canvas.height / 2
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    idlePhaseRef.current += 0.025

    for (let i = 0; i < BARS; i++) {
      const angle = (i / BARS) * Math.PI * 2 - Math.PI / 2
      const wave = Math.sin(idlePhaseRef.current + i * 0.4) * 0.5 + 0.5
      const len = 4 + wave * 8
      const x1 = cx + Math.cos(angle) * INNER_R
      const y1 = cy + Math.sin(angle) * INNER_R
      const x2 = cx + Math.cos(angle) * (INNER_R + len)
      const y2 = cy + Math.sin(angle) * (INNER_R + len)
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.strokeStyle = `rgba(0,245,255,${0.15 + wave * 0.2})`
      ctx.lineWidth = 2
      ctx.lineCap = 'round'
      ctx.stroke()
    }
    idleAnimRef.current = requestAnimationFrame(drawIdle)
  }, [])

  // Live audio-reactive animation
  const drawLive = useCallback((analyser: AnalyserNode) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const cx = canvas.width / 2, cy = canvas.height / 2
    const data = new Uint8Array(analyser.frequencyBinCount)

    const tick = () => {
      analyser.getByteFrequencyData(data)
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Outer glow ring
      const avg = data.reduce((a, b) => a + b, 0) / data.length / 255
      const grad = ctx.createRadialGradient(cx, cy, INNER_R - 4, cx, cy, INNER_R + OUTER_MAX)
      grad.addColorStop(0, `rgba(255,0,110,${avg * 0.4})`)
      grad.addColorStop(1, 'rgba(255,0,110,0)')
      ctx.beginPath()
      ctx.arc(cx, cy, INNER_R + OUTER_MAX * avg, 0, Math.PI * 2)
      ctx.fillStyle = grad
      ctx.fill()

      for (let i = 0; i < BARS; i++) {
        const angle = (i / BARS) * Math.PI * 2 - Math.PI / 2
        const bin = Math.floor((i / BARS) * data.length * 0.7)
        const v = data[bin] / 255
        const len = 4 + v * OUTER_MAX
        const x1 = cx + Math.cos(angle) * INNER_R
        const y1 = cy + Math.sin(angle) * INNER_R
        const x2 = cx + Math.cos(angle) * (INNER_R + len)
        const y2 = cy + Math.sin(angle) * (INNER_R + len)

        const barGrad = ctx.createLinearGradient(x1, y1, x2, y2)
        barGrad.addColorStop(0, `rgba(255,0,110,${0.6 + v * 0.4})`)
        barGrad.addColorStop(1, `rgba(191,0,255,${0.3 + v * 0.4})`)

        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.strokeStyle = barGrad
        ctx.lineWidth = 2.5
        ctx.lineCap = 'round'
        ctx.stroke()
      }
      animFrameRef.current = requestAnimationFrame(tick)
    }
    animFrameRef.current = requestAnimationFrame(tick)
  }, [])

  useEffect(() => {
    if (state === 'idle') {
      cancelAnimationFrame(animFrameRef.current)
      drawIdle()
    } else if (state === 'transcribing') {
      cancelAnimationFrame(idleAnimRef.current)
      cancelAnimationFrame(animFrameRef.current)
      // Clear canvas
      const canvas = canvasRef.current
      if (canvas) canvas.getContext('2d')!.clearRect(0, 0, canvas.width, canvas.height)
    }
    return () => {
      cancelAnimationFrame(idleAnimRef.current)
    }
  }, [state, drawIdle])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const audioCtx = new AudioContext()
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 128
      source.connect(analyser)
      analyserRef.current = analyser

      cancelAnimationFrame(idleAnimRef.current)
      drawLive(analyser)

      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        audioCtx.close()
        cancelAnimationFrame(animFrameRef.current)
        setState('transcribing')
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const text = await transcribeAudio(blob)
        if (text) onTranscript(text)
        setState('idle')
      }
      recorder.start()
      mediaRecorderRef.current = recorder
      setState('recording')
    } catch {
      setState('idle')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    mediaRecorderRef.current = null
  }

  const handleClick = () => {
    if (state === 'idle') startRecording()
    else if (state === 'recording') stopRecording()
  }

  const label = isRecording ? 'Tap to stop' : isTranscribing ? 'Transcribing…' : 'Tap to speak'

  return (
    <div className="flex flex-col gap-3 h-full">
      {/* Transcript box */}
      <div
        ref={transcriptBoxRef}
        className="w-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-xl p-5 text-base text-[#e0e0ff] flex flex-col flex-1"
      >
        {transcript ? (
          <p className="leading-relaxed">{transcript}</p>
        ) : (
          <p className="text-[#2a2a4a] leading-relaxed">
            {isTranscribing ? 'Transcribing your recording…' : 'Your transcribed speech will appear here…'}
          </p>
        )}
      </div>

      {/* Circular visualiser + mic button */}
      <div className="flex flex-col items-center gap-2 py-1">
        <div className="relative flex items-center justify-center" style={{ width: 200, height: 200 }}>
          <canvas
            ref={canvasRef}
            width={200}
            height={200}
            className="absolute inset-0"
          />
          <button
            onClick={handleClick}
            disabled={isTranscribing}
            className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center transition-all duration-500 cursor-pointer border-2 disabled:cursor-not-allowed ${
              isRecording
                ? 'border-[#ff006e] bg-[#ff006e15] shadow-[0_0_40px_#ff006e66]'
                : 'border-[#00f5ff44] bg-[#0a0a0f] hover:border-[#00f5ff88] hover:shadow-[0_0_30px_#00f5ff33]'
            }`}
          >
            {isTranscribing ? (
              <div className="flex gap-1">
                {[0, 1, 2].map((d) => (
                  <span key={d} className="w-1 h-5 rounded-full bg-[#00f5ff] animate-bounce" style={{ animationDelay: `${d * 0.15}s` }} />
                ))}
              </div>
            ) : (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={isRecording ? '#ff006e' : '#00f5ff'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="2" width="6" height="11" rx="3" />
                <path d="M5 10a7 7 0 0 0 14 0" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            )}
          </button>
        </div>
        <p className={`text-xs tracking-[0.3em] uppercase transition-colors duration-300 ${
          isRecording ? 'text-[#ff006e]' : isTranscribing ? 'text-[#00f5ff]' : 'text-[#4a4a6a]'
        }`}>{label}</p>
      </div>
    </div>
  )
}
