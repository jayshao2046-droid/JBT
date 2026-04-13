// 浏览器通知工具 (SIMWEB-01 P1-5)

export async function requestNotificationPermission(): Promise<boolean> {
  if (!("Notification" in window)) {
    console.warn("浏览器不支持桌面通知")
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

export function showNotification(
  title: string,
  body: string,
  level: "info" | "warning" | "error" = "info"
): void {
  if (Notification.permission === "granted") {
    new Notification(title, {
      body,
      icon: level === "error" ? "/alert-icon.png" : "/info-icon.png",
      tag: "sim-trading-alert",
      requireInteraction: level === "error",
    })
  }
}
