// 音频告警工具（从 sim-trading 复用）

let audioContext: AudioContext | null = null
let alertBuffer: AudioBuffer | null = null

export async function initAudio(): Promise<void> {
  if (typeof window === "undefined") return

  try {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()

    // 创建简单的提示音（440Hz 正弦波，持续 200ms）
    const sampleRate = audioContext.sampleRate
    const duration = 0.2
    const buffer = audioContext.createBuffer(1, sampleRate * duration, sampleRate)
    const data = buffer.getChannelData(0)

    for (let i = 0; i < buffer.length; i++) {
      data[i] = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 0.3
    }

    alertBuffer = buffer
  } catch (error) {
    console.error("Failed to initialize audio:", error)
  }
}

export function playAlertSound(): void {
  if (!audioContext || !alertBuffer) {
    initAudio()
    return
  }

  try {
    const source = audioContext.createBufferSource()
    source.buffer = alertBuffer
    source.connect(audioContext.destination)
    source.start()
  } catch (error) {
    console.error("Failed to play alert sound:", error)
  }
}
