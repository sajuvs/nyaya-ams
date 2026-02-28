import { useState, useRef, useEffect, useCallback } from 'react'
import gsap from 'gsap'
import { io, Socket } from 'socket.io-client'
import {
  resampleAudio,
  encodeWAV,
  arrayBufferToBase64,
  calculateAudioEnergy,
} from '../utils/audioUtils'

type RecordState = 'idle' | 'recording' | 'transcribing'

interface Props {
  onTranscript: (text: string) => void
  transcript: string
}

interface TranscriptionResult {
  text: string
  timestamp: number
  chunkName: string
  status: string
}

const BARS = 48
const INNER_R = 52
const OUTER_MAX = 36

export default function VoiceInput({ onTranscript, transcript }: Props) {
  const [state, setState] = useState<RecordState>('idle')
  const [isConnected, setIsConnected] = useState(false)
  
  // Refs for WebSocket transcription
  const socketRef = useRef<Socket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const audioChunksRef = useRef<Int16Array[]>([])
  const lastChunkTimeRef = useRef<number>(0)
  const recordingStartTimeRef = useRef<number>(0)
  const chunkCounterRef = useRef<number>(0)
  const isRecordingRef = useRef<boolean>(false)
  const accumulatedTranscriptRef = useRef<string>('')
  
  // Refs for visualization
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number>(0)
  const transcriptBoxRef = useRef<HTMLDivElement>(null)
  const idleAnimRef = useRef<number>(0)
  const idlePhaseRef = useRef(0)

  const isRecording = state === 'recording'
  const isTranscribing = state === 'transcribing'

  // Initialize WebSocket connection
  useEffect(() => {
    const socket = io('http://localhost:8000', {
      path: '/socket.io',
      transports: ['websocket'],
    })

    socket.on('connect', () => {
      console.log('✅ Connected to transcription service')
      setIsConnected(true)
    })

    socket.on('disconnect', () => {
      console.log('❌ Disconnected from server')
      setIsConnected(false)
    })

    socket.on('transcription_result', (data: TranscriptionResult) => {
      console.log('📥 Received transcription:', data)
      if (data && data.text && data.text.trim()) {
        // Accumulate transcriptions with space separator
        const newText = data.text.trim()
        accumulatedTranscriptRef.current = accumulatedTranscriptRef.current 
          ? `${accumulatedTranscriptRef.current} ${newText}`
          : newText
        onTranscript(accumulatedTranscriptRef.current)
      }
    })

    socket.on('error', (error: { message: string }) => {
      console.error('❌ Socket error:', error)
    })

    socketRef.current = socket

    return () => {
      socket.disconnect()
    }
  }, [onTranscript])

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

  // Send audio chunk to backend
  const sendAudioChunk = useCallback((audioChunks: Int16Array[], timestamp: number) => {
    if (audioChunks.length === 0 || !socketRef.current) return

    // Combine all chunks
    const totalLength = audioChunks.reduce((sum, chunk) => sum + chunk.length, 0)
    const combinedBuffer = new Int16Array(totalLength)
    let offset = 0

    for (const chunk of audioChunks) {
      combinedBuffer.set(chunk, offset)
      offset += chunk.length
    }

    // Resample to 16kHz (required by Sarvam AI)
    const resampledBuffer = resampleAudio(
      combinedBuffer,
      audioContextRef.current!.sampleRate,
      16000
    )

    // Encode as WAV
    const wavBuffer = encodeWAV(resampledBuffer, 16000)

    // Convert to Base64
    const base64Audio = arrayBufferToBase64(wavBuffer)

    // Send to backend
    const chunkName = `chunk_${++chunkCounterRef.current}`
    socketRef.current.emit('audio_chunk', {
      audio: base64Audio,
      timestamp: timestamp,
      chunkName: chunkName,
    })

    console.log(`✅ Sent chunk: ${chunkName}`)
  }, [])

  const startRecording = async () => {
    try {
      if (!isConnected) {
        console.error('❌ Not connected to transcription service')
        return
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      mediaStreamRef.current = stream

      // Create audio context
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
      audioContextRef.current = audioCtx

      const source = audioCtx.createMediaStreamSource(stream)
      
      // Create analyser for visualization
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 128
      source.connect(analyser)
      analyserRef.current = analyser

      // Create processor for transcription
      const processor = audioCtx.createScriptProcessor(4096, 1, 1)
      processorRef.current = processor

      audioChunksRef.current = []
      lastChunkTimeRef.current = Date.now()
      recordingStartTimeRef.current = Date.now()
      chunkCounterRef.current = 0
      // Note: We DON'T reset accumulatedTranscriptRef here
      // This allows multiple recording sessions to append

      processor.onaudioprocess = (event) => {
        if (!isRecordingRef.current) return

        const audioData = event.inputBuffer.getChannelData(0)
        const int16Array = new Int16Array(audioData.length)

        // Convert to Int16 and check for voice activity
        const energy = calculateAudioEnergy(audioData)

        for (let i = 0; i < audioData.length; i++) {
          int16Array[i] = audioData[i] * 32767
        }

        // Only add chunk if there's significant audio
        if (energy > 0.01) {
          audioChunksRef.current.push(int16Array)
        }

        const currentTime = Date.now()
        const elapsed = (currentTime - recordingStartTimeRef.current) / 1000
        const timeSinceLastChunk = currentTime - lastChunkTimeRef.current

        // Send chunks every 2 seconds
        if (timeSinceLastChunk >= 2000 && audioChunksRef.current.length > 0) {
          const chunksToSend = [...audioChunksRef.current]
          audioChunksRef.current = []
          sendAudioChunk(chunksToSend, elapsed)
          lastChunkTimeRef.current = currentTime
        }
      }

      source.connect(processor)
      processor.connect(audioCtx.destination)

      cancelAnimationFrame(idleAnimRef.current)
      drawLive(analyser)

      setState('recording')
      isRecordingRef.current = true
      console.log('✅ Recording started. Transcript will append to existing content.')
    } catch (error) {
      console.error('❌ Error accessing microphone:', error)
      setState('idle')
    }
  }

  const stopRecording = () => {
    isRecordingRef.current = false
    setState('idle')

    // Stop processor
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }

    // Stop analyser (but keep the reference for next recording)
    if (analyserRef.current) {
      analyserRef.current.disconnect()
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }

    cancelAnimationFrame(animFrameRef.current)
    
    // Note: We DON'T reset accumulatedTranscriptRef here
    // This allows multiple recording sessions to append to the same transcript
    console.log('Recording stopped. Transcript preserved for next session.')
  }

  const handleClick = () => {
    if (state === 'idle') {
      startRecording()
    } else if (state === 'recording') {
      stopRecording()
    }
    // Note: transcribing state is disabled, so button is always clickable
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
            disabled={isTranscribing || !isConnected}
            className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center transition-all duration-500 cursor-pointer border-2 disabled:cursor-not-allowed disabled:opacity-50 ${
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
