"use client"

import { useEffect, useRef } from "react"

export function AnimatedGridBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // ── Config ──────────────────────────────────────────────
    const HEX_R     = 16        // hex radius
    const WAVE_AMP  = 2.8       // wave distortion strength
    const WAVE_SPD  = 0.00055   // animation speed scalar
    const BASE_A    = 0.05      // base line alpha
    const SHIMMER_A = 0.18      // peak shimmer alpha

    // Electric pulse config
    const MAX_PULSES      = 10
    const PULSE_PROB      = 0.025  // per-frame spawn probability
    const PULSE_TRAIL     = 12     // trail length in segments

    // Radial glow sources (anchor positions as fractions of viewport)
    const GLOW_SOURCES = [
      { fx: 0.25, fy: 0.35 },
      { fx: 0.72, fy: 0.60 },
      { fx: 0.50, fy: 0.10 },
    ]

    // Orange/amber palette
    const ORANGE_CORE  = (a: number) => `hsla(28,  100%, 62%, ${a})`
    const AMBER_MID    = (a: number) => `hsla(38,  95%,  55%, ${a})`
    const GOLD_EDGE    = (a: number) => `hsla(48,  90%,  50%, ${a})`

    // ── State ────────────────────────────────────────────────
    let W = 0, H = 0
    const sqrt3 = Math.sqrt(3)
    const hexW  = sqrt3 * HEX_R          // horizontal hex pitch
    const hexVD = HEX_R * 1.5            // vertical hex pitch

    let hexCenters: { x: number; y: number }[] = []

    interface Pulse {
      path:      { x: number; y: number }[]
      timer:     number   // frames since last hop
      dir:       number   // 0-5
      age:       number
      maxAge:    number
      hue:       number   // slight hue variation per pulse
      speed:     number   // frames per hop (lower = faster)
    }
    let pulses: Pulse[] = []

    // ── Resize ───────────────────────────────────────────────
    function resize() {
      W = window.innerWidth
      H = window.innerHeight
      canvas!.width  = W
      canvas!.height = H
      buildHexGrid()
    }

    function buildHexGrid() {
      hexCenters = []
      const cols = Math.ceil(W / hexW) + 3
      const rows = Math.ceil(H / hexVD) + 3
      for (let row = -1; row <= rows; row++) {
        for (let col = -1; col <= cols; col++) {
          const x = col * hexW + (row % 2 !== 0 ? hexW / 2 : 0)
          const y = row * hexVD
          hexCenters.push({ x, y })
        }
      }
    }

    // ── Hex geometry with wave displacement ──────────────────
    function hexVerts(cx: number, cy: number, t: number) {
      const verts: { x: number; y: number }[] = []
      for (let i = 0; i < 6; i++) {
        const ang = (Math.PI / 3) * i - Math.PI / 6
        const bx  = cx + HEX_R * Math.cos(ang)
        const by  = cy + HEX_R * Math.sin(ang)

        // Two-frequency wave — different phase per axis for organic feel
        const dx =
          Math.sin(by * 0.022 + t * 1.3 + bx * 0.009) * WAVE_AMP +
          Math.sin(bx * 0.013 + t * 0.7               ) * WAVE_AMP * 0.45
        const dy =
          Math.sin(bx * 0.019 + t * 1.0 + by * 0.011) * WAVE_AMP +
          Math.cos(by * 0.016 + t * 1.4               ) * WAVE_AMP * 0.4

        verts.push({ x: bx + dx, y: by + dy })
      }
      return verts
    }

    // ── Radial influence of glow source on a hex ─────────────
    function glowInfluence(cx: number, cy: number, t: number): number {
      let total = 0
      for (const g of GLOW_SOURCES) {
        const gx = g.fx * W + Math.sin(t * 0.4 + g.fy * 5) * W * 0.06
        const gy = g.fy * H + Math.cos(t * 0.35 + g.fx * 5) * H * 0.06
        const dist = Math.hypot(cx - gx, cy - gy)
        const radius = Math.min(W, H) * 0.40
        total += Math.max(0, 1 - dist / radius) ** 2
      }
      return Math.min(total, 1)
    }

    // ── Pulse management ─────────────────────────────────────
    function spawnPulse() {
      if (pulses.length >= MAX_PULSES) return
      const idx   = Math.floor(Math.random() * hexCenters.length)
      const start = hexCenters[idx]
      // Random speed: 30% chance fast (0.6-1.2), 50% medium (1.5-2.5), 20% slow (3-5)
      const roll = Math.random()
      let speed: number
      if (roll < 0.3) {
        speed = 0.6 + Math.random() * 0.6   // fast burst
      } else if (roll < 0.8) {
        speed = 1.5 + Math.random() * 1.0   // medium
      } else {
        speed = 3.0 + Math.random() * 2.0   // slow crawl
      }

      pulses.push({
        path:   [{ x: start.x, y: start.y }],
        timer:  0,
        dir:    Math.floor(Math.random() * 6),
        age:    0,
        maxAge: 120 + Math.random() * 200,
        hue:    22 + Math.random() * 28,   // 22-50°: orange to gold
        speed,
      })
    }

    function updatePulses() {
      pulses = pulses.filter((p) => {
        p.age++
        p.timer++

        if (p.timer >= p.speed) {
          p.timer = 0
          // ~30% chance to bend direction
          if (Math.random() < 0.28) {
            p.dir = (p.dir + (Math.random() > 0.5 ? 1 : 5)) % 6
          }
          const last = p.path[p.path.length - 1]
          const ang  = (Math.PI / 3) * p.dir
          const nx   = last.x + hexW * Math.cos(ang)
          const ny   = last.y + hexW * Math.sin(ang)
          p.path.push({ x: nx, y: ny })
        }

        if (p.path.length > PULSE_TRAIL) p.path.shift()

        // Kill if off-screen or expired
        const tail = p.path[p.path.length - 1]
        if (
          tail.x < -150 || tail.x > W + 150 ||
          tail.y < -150 || tail.y > H + 150 ||
          p.age > p.maxAge
        ) return false

        return true
      })
    }

    function drawPulses() {
      if (!ctx) return
      for (const p of pulses) {
        if (p.path.length < 2) continue

        const fade = Math.min(1, (p.maxAge - p.age) / 40)  // fade out at end
        const head = p.path[p.path.length - 1]
        const tail = p.path[0]

        // Outer glow pass
        ctx.beginPath()
        ctx.moveTo(tail.x, tail.y)
        for (let i = 1; i < p.path.length; i++) {
          const pt = p.path[i]
          ctx.lineTo(
            pt.x + (Math.random() - 0.5) * 1.2,
            pt.y + (Math.random() - 0.5) * 1.2
          )
        }
        const gGlow = ctx.createLinearGradient(tail.x, tail.y, head.x, head.y)
        gGlow.addColorStop(0,   `hsla(${p.hue}, 100%, 60%, 0)`)
        gGlow.addColorStop(0.5, `hsla(${p.hue}, 100%, 65%, ${0.12 * fade})`)
        gGlow.addColorStop(1,   `hsla(${p.hue}, 100%, 70%, ${0.25 * fade})`)
        ctx.strokeStyle = gGlow
        ctx.lineWidth   = 6
        ctx.lineCap     = "round"
        ctx.lineJoin    = "round"
        ctx.stroke()

        // Core bright arc
        ctx.beginPath()
        ctx.moveTo(tail.x, tail.y)
        for (let i = 1; i < p.path.length; i++) {
          const pt = p.path[i]
          ctx.lineTo(
            pt.x + (Math.random() - 0.5) * 1.8,
            pt.y + (Math.random() - 0.5) * 1.8
          )
        }
        const gCore = ctx.createLinearGradient(tail.x, tail.y, head.x, head.y)
        gCore.addColorStop(0,   `hsla(${p.hue}, 100%, 72%, 0)`)
        gCore.addColorStop(0.4, `hsla(${p.hue}, 100%, 75%, ${0.45 * fade})`)
        gCore.addColorStop(1,   `hsla(${p.hue + 10}, 100%, 80%, ${0.85 * fade})`)
        ctx.strokeStyle = gCore
        ctx.lineWidth   = 1.2
        ctx.stroke()

        // Bright head dot
        const headGlow = ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, 8)
        headGlow.addColorStop(0,   `hsla(${p.hue + 15}, 100%, 90%, ${0.7 * fade})`)
        headGlow.addColorStop(0.4, `hsla(${p.hue},      100%, 70%, ${0.3 * fade})`)
        headGlow.addColorStop(1,   `hsla(${p.hue},      100%, 60%, 0)`)
        ctx.beginPath()
        ctx.arc(head.x, head.y, 8, 0, Math.PI * 2)
        ctx.fillStyle = headGlow
        ctx.fill()
      }
    }

    // ── Radial glow scatter (background haze) ────────────────
    function drawGlowHaze(t: number) {
      if (!ctx) return
      for (const g of GLOW_SOURCES) {
        const gx = g.fx * W + Math.sin(t * 0.4 + g.fy * 5) * W * 0.06
        const gy = g.fy * H + Math.cos(t * 0.35 + g.fx * 5) * H * 0.06
        const r  = Math.min(W, H) * 0.38

        // Breathe in/out
        const breathe = 0.5 + 0.5 * Math.sin(t * 0.6 + g.fx * 8)

        const rg = ctx.createRadialGradient(gx, gy, 0, gx, gy, r)
        rg.addColorStop(0,    ORANGE_CORE(0.055 * breathe))
        rg.addColorStop(0.35, AMBER_MID  (0.030 * breathe))
        rg.addColorStop(0.65, GOLD_EDGE  (0.012 * breathe))
        rg.addColorStop(1,    `hsla(40,90%,50%,0)`)

        ctx.beginPath()
        ctx.arc(gx, gy, r, 0, Math.PI * 2)
        ctx.fillStyle = rg
        ctx.fill()
      }
    }

    // ── Main draw loop ────────────────────────────────────────
    const startTime = performance.now()

    function draw(now: number) {
      if (!ctx) return
      const t = (now - startTime) * WAVE_SPD

      ctx.clearRect(0, 0, W, H)

      // 1. Radial ambient glow hazes
      drawGlowHaze(t)

      // 2. Maybe spawn a new pulse
      if (Math.random() < PULSE_PROB) spawnPulse()
      updatePulses()

      // 3. Honeycomb grid
      for (const { x: cx, y: cy } of hexCenters) {
        const verts = hexVerts(cx, cy, t)

        // Per-hex shimmer: wave + glow proximity
        const wave   = 0.5 + 0.5 * (
          Math.sin(cx * 0.018 + t * 1.5) * Math.sin(cy * 0.014 + t * 1.1)
        )
        const glow   = glowInfluence(cx, cy, t)
        const alpha  = BASE_A + wave * 0.04 + glow * (SHIMMER_A - BASE_A)

        // Color shifts from grey-orange in dim areas to vivid orange near glow
        const hue  = 25 + glow * 18          // 25 → 43°
        const sat  = 30 + glow * 70          // 30 → 100%
        const lum  = 50 + glow * 20          // 50 → 70%

        ctx.beginPath()
        ctx.moveTo(verts[0].x, verts[0].y)
        for (let i = 1; i < 6; i++) ctx.lineTo(verts[i].x, verts[i].y)
        ctx.closePath()

        ctx.strokeStyle = `hsla(${hue.toFixed(0)}, ${sat.toFixed(0)}%, ${lum.toFixed(0)}%, ${alpha.toFixed(3)})`
        ctx.lineWidth   = 0.6 + glow * 0.5
        ctx.stroke()

        // Near-glow hexes get a faint inner fill for depth
        if (glow > 0.25) {
          ctx.fillStyle = ORANGE_CORE(glow * 0.022)
          ctx.fill()
        }
      }

      // 4. Electric pulses on top
      drawPulses()

      rafRef.current = requestAnimationFrame(draw)
    }

    resize()
    window.addEventListener("resize", resize)
    rafRef.current = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener("resize", resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 opacity-0 animate-fade-in"
      style={{
        display: "block",
        animation: "fadeIn 0.8s ease-in forwards"
      }}
    />
  )
}
