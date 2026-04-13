// 音频播放工具 (SIMWEB-01 P1-5)

let alertAudio: HTMLAudioElement | null = null

export function initAudio(): void {
  if (typeof window !== "undefined" && !alertAudio) {
    alertAudio = new Audio("/alert.mp3")
    alertAudio.preload = "auto"
  }
}

export function playAlertSound(): void {
  if (alertAudio) {
    alertAudio.currentTime = 0
    alertAudio.play().catch((err) => {
      console.warn("音频播放失败（可能需要用户交互）:", err)
    })
  }
}

export function stopAlertSound(): void {
  if (alertAudio) {
    alertAudio.pause()
    alertAudio.currentTime = 0
  }
}
