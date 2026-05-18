import { motion } from 'framer-motion'

export default function RiskHeatmap({ heatmap, trajectories }) {
  const cells = heatmap?.slice(0, 48) ?? []
  const maxIntensity = Math.max(...cells.map((c) => c.intensity), 0.01)

  return (
    <motion.section layout className="glass-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-sentinel-muted mb-3">
        Predictive Risk Heatmap
      </h2>
      <div className="grid grid-cols-8 gap-1 mb-3">
        {cells.length === 0
          ? Array.from({ length: 24 }).map((_, i) => (
              <div
                key={i}
                className="aspect-square rounded bg-sentinel-border/30 animate-pulse"
              />
            ))
          : cells.map((z, i) => (
              <motion.div
                key={i}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="aspect-square rounded relative group"
                style={{
                  background: `rgba(255, 71, 87, ${0.15 + (z.intensity / maxIntensity) * 0.75})`,
                  boxShadow:
                    z.intensity > 0.5
                      ? `0 0 12px rgba(255,71,87,${z.intensity * 0.5})`
                      : 'none',
                }}
                title={`${z.label}: ${(z.intensity * 100).toFixed(0)}%`}
              />
            ))}
      </div>
      <p className="text-xs text-sentinel-muted font-mono">
        {trajectories
          ? `${Object.keys(trajectories).length} predicted paths · 5s horizon`
          : 'Awaiting trajectory data…'}
      </p>
    </motion.section>
  )
}
