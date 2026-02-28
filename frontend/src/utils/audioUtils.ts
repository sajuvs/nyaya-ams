/**
 * Audio utility functions for recording and processing audio chunks
 */

/**
 * Resample audio buffer to target sample rate
 */
export function resampleAudio(
  audioBuffer: Int16Array,
  sourceSampleRate: number,
  targetSampleRate: number
): Int16Array {
  if (sourceSampleRate === targetSampleRate) return audioBuffer;

  const ratio = sourceSampleRate / targetSampleRate;
  const outputLength = Math.floor(audioBuffer.length / ratio);
  const output = new Int16Array(outputLength);

  for (let i = 0; i < outputLength; i++) {
    output[i] = audioBuffer[Math.floor(i * ratio)];
  }

  return output;
}

/**
 * Encode audio buffer as WAV format
 */
export function encodeWAV(audioBuffer: Int16Array, sampleRate: number): ArrayBuffer {
  const length = audioBuffer.length;
  const arrayBuffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(arrayBuffer);

  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  // WAV header
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true); // 16-bit
  writeString(36, 'data');
  view.setUint32(40, length * 2, true);

  // Audio data
  const audioData = new Int16Array(arrayBuffer, 44);
  audioData.set(audioBuffer);

  return arrayBuffer;
}

/**
 * Convert ArrayBuffer to Base64 string
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const uint8Array = new Uint8Array(buffer);
  let binaryString = '';
  const chunkSize = 8192;

  for (let i = 0; i < uint8Array.length; i += chunkSize) {
    const chunk = uint8Array.slice(i, i + chunkSize);
    binaryString += String.fromCharCode.apply(null, Array.from(chunk));
  }

  return btoa(binaryString);
}

/**
 * Format seconds to MM:SS
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Calculate audio energy (for voice activity detection)
 */
export function calculateAudioEnergy(audioData: Float32Array): number {
  let energy = 0;
  for (let i = 0; i < audioData.length; i++) {
    energy += Math.abs(audioData[i]);
  }
  return energy / audioData.length;
}
