import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import {
  resampleAudio,
  encodeWAV,
  arrayBufferToBase64,
  formatTime,
  calculateAudioEnergy,
} from '../utils/audioUtils';

interface TranscriptionResult {
  text: string;
  timestamp: number;
  chunkName: string;
  status: string;
  processedAt?: string;
}

export default function TranscriptPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('Ready to transcribe');
  const [transcriptions, setTranscriptions] = useState<TranscriptionResult[]>([]);
  const [chunksProcessed, setChunksProcessed] = useState(0);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);

  // Refs
  const socketRef = useRef<Socket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioChunksRef = useRef<Int16Array[]>([]);
  const lastChunkTimeRef = useRef<number>(0);
  const recordingStartTimeRef = useRef<number>(0);
  const chunkCounterRef = useRef<number>(0);
  const timeIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const isRecordingRef = useRef<boolean>(false);

  // Initialize WebSocket connection
  useEffect(() => {
    const socket = io('http://localhost:8000', {
      path: '/socket.io',
      transports: ['websocket'],
    });

    socket.on('connect', () => {
      console.log('✅ Connected to transcription service');
      setIsConnected(true);
      setStatus('Connected to transcription service');
    });

    socket.on('disconnect', () => {
      console.log('❌ Disconnected from server');
      setIsConnected(false);
      setStatus('Disconnected from server');
    });

    socket.on('status', (data: { message: string }) => {
      console.log('Status:', data.message);
    });

    socket.on('transcription_result', (data: TranscriptionResult) => {
      console.log('📥 Received transcription:', data);
      if (data && data.text && data.text.trim()) {
        console.log(`✅ Adding transcription to UI: "${data.text}"`);
        setTranscriptions((prev) => [...prev, data]);
      } else {
        console.log('⚠️ Received empty or invalid transcription:', data);
      }
    });

    socket.on('transcription_status', (data: { status: string; chunkName: string }) => {
      console.log('Transcription status:', data);
    });

    socket.on('error', (error: { message: string }) => {
      console.error('❌ Socket error:', error);
      setStatus(`Error: ${error.message}`);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, []);

  // Update recording time
  useEffect(() => {
    if (isRecording) {
      timeIntervalRef.current = setInterval(() => {
        const elapsed = (Date.now() - recordingStartTimeRef.current) / 1000;
        setRecordingTime(elapsed);
      }, 100);
    } else {
      if (timeIntervalRef.current) {
        clearInterval(timeIntervalRef.current);
        timeIntervalRef.current = null;
      }
    }

    return () => {
      if (timeIntervalRef.current) {
        clearInterval(timeIntervalRef.current);
      }
    };
  }, [isRecording]);

  // Visualize audio level
  const visualizeAudio = () => {
    if (!analyserRef.current || !isRecordingRef.current) {
      setAudioLevel(0);
      return;
    }

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    const percentage = Math.min(100, (average / 128) * 100);

    setAudioLevel(percentage);

    animationFrameRef.current = requestAnimationFrame(visualizeAudio);
  };

  // Send audio chunk to backend
  const sendAudioChunk = (audioChunks: Int16Array[], timestamp: number) => {
    if (audioChunks.length === 0 || !socketRef.current) return;

    console.log(`📤 sendAudioChunk called with ${audioChunks.length} chunks, timestamp: ${timestamp.toFixed(2)}s`);

    // Combine all chunks
    const totalLength = audioChunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const combinedBuffer = new Int16Array(totalLength);
    let offset = 0;

    for (const chunk of audioChunks) {
      combinedBuffer.set(chunk, offset);
      offset += chunk.length;
    }

    console.log(`🔗 Combined buffer size: ${totalLength} samples (${(totalLength / 16000).toFixed(2)}s of audio)`);

    // Resample to 16kHz (required by AM-S AI)
    const resampledBuffer = resampleAudio(
      combinedBuffer,
      audioContextRef.current!.sampleRate,
      16000
    );

    console.log(`🔄 Resampled from ${audioContextRef.current!.sampleRate}Hz to 16000Hz, new size: ${resampledBuffer.length} samples`);

    // Encode as WAV
    const wavBuffer = encodeWAV(resampledBuffer, 16000);

    // Convert to Base64
    const base64Audio = arrayBufferToBase64(wavBuffer);

    console.log(`📦 WAV encoded, Base64 size: ${base64Audio.length} characters`);

    // Send to backend
    const chunkName = `chunk_${++chunkCounterRef.current}`;
    socketRef.current.emit('audio_chunk', {
      audio: base64Audio,
      timestamp: timestamp,
      chunkName: chunkName,
    });

    setChunksProcessed(chunkCounterRef.current);
    console.log(`✅ Sent chunk: ${chunkName} (total chunks sent: ${chunkCounterRef.current})`);
  };

  // Start recording
  const startRecording = async () => {
    try {
      console.log('🎙️ Requesting microphone access...');
      setStatus('Requesting microphone access...');

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      console.log('✅ Microphone access granted');
      mediaStreamRef.current = stream;

      // Create audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioContext;

      const mediaStreamSource = audioContext.createMediaStreamSource(stream);

      // Create analyser for visualization
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      mediaStreamSource.connect(analyser);
      analyserRef.current = analyser;

      // Create processor
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      audioChunksRef.current = [];
      lastChunkTimeRef.current = Date.now();
      recordingStartTimeRef.current = Date.now();
      chunkCounterRef.current = 0;

      processor.onaudioprocess = (event) => {
        if (!isRecordingRef.current) return;

        const audioData = event.inputBuffer.getChannelData(0);
        const int16Array = new Int16Array(audioData.length);

        // Convert to Int16 and check for voice activity
        const energy = calculateAudioEnergy(audioData);

        for (let i = 0; i < audioData.length; i++) {
          int16Array[i] = audioData[i] * 32767;
        }

        // Only add chunk if there's significant audio (threshold: 0.01)
        if (energy > 0.01) {
          audioChunksRef.current.push(int16Array);
          console.log(`🎤 Audio detected, energy: ${energy.toFixed(4)}, chunks accumulated: ${audioChunksRef.current.length}`);
        }

        const currentTime = Date.now();
        const elapsed = (currentTime - recordingStartTimeRef.current) / 1000;
        const timeSinceLastChunk = currentTime - lastChunkTimeRef.current;

        // Send chunks every 2 seconds
        if (timeSinceLastChunk >= 2000) {
          console.log(`⏰ 2 seconds elapsed (${timeSinceLastChunk}ms), accumulated chunks: ${audioChunksRef.current.length}`);
          if (audioChunksRef.current.length > 0) {
            const chunksToSend = [...audioChunksRef.current];
            audioChunksRef.current = [];
            console.log(`📦 Sending ${chunksToSend.length} audio chunks to backend`);
            sendAudioChunk(chunksToSend, elapsed);
          } else {
            console.log(`⚠️ No audio chunks to send (silence or low energy)`);
          }
          lastChunkTimeRef.current = currentTime;
        }
      };

      mediaStreamSource.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      isRecordingRef.current = true;
      setStatus('Recording... Transcription active');
      setTranscriptions([]);
      setChunksProcessed(0);
      setRecordingTime(0);

      // Start visualization
      visualizeAudio();

      console.log('✅ Recording started');
    } catch (error) {
      console.error('❌ Error accessing microphone:', error);
      setStatus('Microphone access denied');
      alert('Microphone access denied. Please allow microphone access and try again.');
    }
  };

  // Stop recording
  const stopRecording = () => {
    setIsRecording(false);
    isRecordingRef.current = false;

    // Stop processor
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    // Stop analyser
    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    // Stop animation
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    setAudioLevel(0);
    setStatus('Recording stopped');
    console.log('⏹️ Recording stopped');
  };

  // Toggle recording
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0f] via-[#1a1a2e] to-[#0a0a0f] text-[#e0e0ff]">
      <div className="container mx-auto px-8 py-12 max-w-6xl">
        {/* Header */}
        <header className="mb-12 text-center">
          <h1 className="text-5xl font-bold mb-4">
            <span className="neon-cyan text-[#00f5ff]">🎤</span> Live Audio Transcription
          </h1>
          <p className="text-[#8a8aa0] text-lg">
            Powered by AM-S AI Streaming
          </p>
        </header>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Microphone Section */}
          <div className="bg-[#16162a] rounded-2xl p-8 border border-[#2a2a4a] shadow-2xl">
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
              <span className="text-3xl">🎙️</span>
              Microphone Input
            </h2>

            {/* Microphone Visualizer */}
            <div className="mb-8 text-center">
              <div
                className={`inline-block text-8xl mb-4 transition-all duration-300 ${
                  isRecording ? 'animate-pulse text-red-500' : 'text-[#4a4a6a]'
                }`}
              >
                🎤
              </div>

              {/* Audio Level Bar */}
              <div className="w-full h-4 bg-[#0a0a0f] rounded-full overflow-hidden mb-4">
                <div
                  className="h-full bg-gradient-to-r from-[#00f5ff] to-[#bf00ff] transition-all duration-100"
                  style={{ width: `${audioLevel}%` }}
                />
              </div>

              <p className="text-[#8a8aa0] text-sm">
                {isRecording
                  ? 'Recording... Transcription active'
                  : 'Click "Start Recording" to begin'}
              </p>
            </div>

            {/* Controls */}
            <div className="space-y-4">
              <button
                onClick={toggleRecording}
                disabled={!isConnected}
                className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-300 ${
                  isRecording
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-gradient-to-r from-[#00f5ff] to-[#bf00ff] hover:opacity-90 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg`}
              >
                {isRecording ? '⏹️ Stop Recording' : '🎙️ Start Recording'}
              </button>

              {/* Status */}
              <div className="flex items-center justify-center gap-2 text-sm">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span className="text-[#8a8aa0]">{status}</span>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[#2a2a4a]">
                <div className="text-center">
                  <div className="text-2xl font-bold text-[#00f5ff]">{chunksProcessed}</div>
                  <div className="text-xs text-[#8a8aa0]">Chunks Processed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-[#bf00ff]">
                    {formatTime(recordingTime)}
                  </div>
                  <div className="text-xs text-[#8a8aa0]">Recording Time</div>
                </div>
              </div>
            </div>
          </div>

          {/* Transcription Section */}
          <div className="bg-[#16162a] rounded-2xl p-8 border border-[#2a2a4a] shadow-2xl">
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
              <span className="text-3xl">📝</span>
              Live Transcription
            </h2>

            {/* Transcription Output */}
            <div className="bg-[#0a0a0f] rounded-xl p-6 h-[400px] overflow-y-auto border border-[#2a2a4a] custom-scrollbar">
              {transcriptions.length === 0 ? (
                <p className="text-[#4a4a6a] text-center py-8">
                  Transcriptions will appear here in real-time...
                </p>
              ) : (
                <div className="space-y-4">
                  {transcriptions.map((item, index) => (
                    <div
                      key={index}
                      className="bg-[#16162a] rounded-lg p-4 border border-[#2a2a4a] animate-fade-in"
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-[#00f5ff] text-xs font-mono whitespace-nowrap">
                          [{formatTime(item.timestamp)}]
                        </span>
                        <span className="text-[#e0e0ff] flex-1">{item.text}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Transcription Stats */}
            <div className="mt-4 text-center text-sm text-[#8a8aa0]">
              Total transcriptions: {transcriptions.length}
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-[#4a4a6a] text-sm">
          <p>Demo: Real-time speech-to-text using AM-S AI</p>
        </footer>
      </div>

      {/* Custom Styles */}
      <style>{`
        .neon-cyan {
          text-shadow: 0 0 10px #00f5ff, 0 0 20px #00f5ff, 0 0 30px #00f5ff;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0a0a0f;
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #00f5ff, #bf00ff);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #00d4dd, #9f00dd);
        }

        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
