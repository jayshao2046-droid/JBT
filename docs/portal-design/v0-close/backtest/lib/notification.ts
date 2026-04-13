// 通知工具（从 sim-trading 复用）

export async function requestNotificationPermission(): Promise<boolean> {
  if (!("Notification" in window)) {
    console.warn("浏览器不支持通知")
    return false
  }

  if (Notification.permission === "granted") {
    return true
  }

  if (Notification.permission !== "denied") {
    const permission = await Notification.requestPermission()
    return permission === "granted"
  }

  return false
}

export function showNotification(title: string, options?: NotificationOptions): void {
  if (Notification.permission === "granted") {
    new Notification(title, options)
  }
}
