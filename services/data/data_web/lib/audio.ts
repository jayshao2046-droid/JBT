"""音频告警工具"""

let audioContext: AudioContext | null = null
let alertBuffer: AudioBuffer | null = null

export async function initAudio(): Promise<void> {
  if (typeof window === 'undefined') return

  try {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()

    // 生成简单的提示音（440Hz 正弦波，持续 200ms）
    const sampleRate = audioContext.sampleRate
    const duration = 0.2
    const buffer = audioContext.createBuffer(1, sampleRate * duration, sampleRate)
    const data = buffer.getChannelData(0)

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate
      data[i] = Math.sin(2 * Math.PI * 440 * t) * Math.exp(-t * 5)
    }

    alertBuffer = buffer
  } catch (error) {
    console.error('音频初始化失败:', error)
  }
}

export function playAlertSound(): void {
  if (!audioContext || !alertBuffer) {
    console.warn('音频未初始化')
    return
  }

  try {
    const source = audioContext.createBufferSource()
    source.buffer = alertBuffer
    source.connect(audioContext.destination)
    source.start(0)
  } catch (error) {
    console.error('播放音频失败:', error)
  }
}
