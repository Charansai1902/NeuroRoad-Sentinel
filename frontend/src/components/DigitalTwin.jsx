import { motion } from 'framer-motion'
import { useEffect, useRef } from 'react'

const W = 640
const H = 360

function drawScene(ctx, frame) {
  ctx.fillStyle = '#0d1219'
  ctx.fillRect(0, 0, W, H)

  // Road
  const grad = ctx.createLinearGradient(0, 0, 0, H)
  grad.addColorStop(0, '#1a2535')
  grad.addColorStop(1, '#0d1219')
  ctx.fillStyle = grad
  ctx.fillRect(W * 0.25, 0, W * 0.5, H)

  ctx.strokeStyle = 'rgba(255,255,255,0.15)'
  ctx.setLineDash([12, 16])
  ctx.beginPath()
  ctx.moveTo(W / 2, 0)
  ctx.lineTo(W / 2, H)
  ctx.stroke()
  ctx.setLineDash([])

  // Ego vehicle
  ctx.fillStyle = '#00d4aa'
  ctx.shadowColor = '#00d4aa'
  ctx.shadowBlur = 12
  ctx.fillRect(W / 2 - 14, H - 70, 28, 48)
  ctx.shadowBlur = 0

  // Trajectories
  if (frame?.trajectories) {
    Object.entries(frame.trajectories).forEach(([key, pts], idx) => {
      if (!pts?.length) return
      const isEgo = key === 'ego'
      ctx.strokeStyle = isEgo ? '#00d4aa' : '#ffb020'
      ctx.lineWidth = isEgo ? 2 : 1.5
      ctx.globalAlpha = 0.85
      ctx.beginPath()
      pts.forEach((p, i) => {
        const sx = W / 2 + p.x * 2.5
        const sy = H - 60 - p.y * 2.2
        if (i === 0) ctx.moveTo(sx, sy)
        else ctx.lineTo(sx, sy)
      })
      ctx.stroke()
      ctx.globalAlpha = 1
    })
  }

  // Risk heatmap zones
  frame?.risk_heatmap?.forEach((z) => {
    const sx = W / 2 + z.x * 2.5
    const sy = H - 60 - z.y * 2.2
    const r = 8 + z.intensity * 22
    const g = ctx.createRadialGradient(sx, sy, 0, sx, sy, r)
    const a = z.intensity * 0.55
    g.addColorStop(0, `rgba(255, 71, 87, ${a})`)
    g.addColorStop(1, 'rgba(255, 71, 87, 0)')
    ctx.fillStyle = g
    ctx.beginPath()
    ctx.arc(sx, sy, r, 0, Math.PI * 2)
    ctx.fill()
  })

  // Detections (top-down projection)
  frame?.detections?.forEach((d) => {
    const cx = ((d.x1 + d.x2) / 2 / 640) * W
    const cy = ((d.y1 + d.y2) / 2 / 480) * H * 0.7 + H * 0.15
    ctx.fillStyle = d.class_name === 'person' ? '#ff4757' : '#4dabf7'
    ctx.beginPath()
    ctx.arc(W / 2 + (cx - W / 2) * 0.5, cy, 8, 0, Math.PI * 2)
    ctx.fill()
  })

  // V2V
  frame?.v2v_messages?.forEach((v) => {
    const sx = W / 2 + v.position[0] * 2
    const sy = H - 80 - v.position[1] * 1.5
    ctx.strokeStyle = v.sudden_brake ? '#ff4757' : '#6b7c93'
    ctx.strokeRect(sx - 10, sy - 6, 20, 12)
  })
}

export default function DigitalTwin({ frame }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const ctx = canvasRef.current?.getContext('2d')
    if (ctx) drawScene(ctx, frame)
  }, [frame])

  const collisionProb = frame?.metadata?.collision_probability ?? 0
  const ttc = frame?.metadata?.time_to_collision_sec

  return (
    <motion.section
      layout
      className="glass-panel glow-accent p-4"
    >
      <motion.div className="flex justify-between items-center mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-sentinel-muted">
          Digital Twin — Bird&apos;s Eye
        </h2>
        <div className="flex gap-4 text-xs font-mono">
          <span>
            Collision:{' '}
            <span
              className={
                collisionProb > 0.6
                  ? 'text-sentinel-danger'
                  : collisionProb > 0.35
                    ? 'text-sentinel-warn'
                    : 'text-sentinel-accent'
              }
            >
              {(collisionProb * 100).toFixed(0)}%
            </span>
          </span>
          {ttc != null && (
            <span>
              TTC: <span className="text-white">{ttc.toFixed(1)}s</span>
            </span>
          )}
          <span>
            Intent:{' '}
            <span className="text-sentinel-accent">
              {frame?.metadata?.driver_intent ?? '—'}
            </span>
          </span>
        </div>
      </motion.div>
      <canvas
        ref={canvasRef}
        width={W}
        height={H}
        className="w-full rounded-lg border border-sentinel-border"
      />
    </motion.section>
  )
}
