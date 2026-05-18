import { motion } from 'framer-motion'

export default function V2VPanel({ messages }) {
  const list = messages ?? []

  return (
    <motion.section layout className="glass-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-sentinel-muted mb-3">
        V2V Cooperative Intelligence
      </h2>
      <ul className="space-y-2 max-h-40 overflow-y-auto">
        {list.length === 0 ? (
          <li className="text-sm text-sentinel-muted">No V2V messages</li>
        ) : (
          list.map((m) => (
            <li
              key={m.vehicle_id}
              className={`text-xs font-mono rounded border px-2 py-2 ${
                m.sudden_brake
                  ? 'border-sentinel-danger/40 bg-sentinel-danger/10'
                  : 'border-sentinel-border bg-sentinel-bg/40'
              }`}
            >
              <span className="text-sentinel-accent">{m.vehicle_id}</span>
              <span className="text-sentinel-muted mx-2">·</span>
              {m.speed_kmh.toFixed(0)} km/h
              <span className="text-sentinel-muted mx-2">·</span>
              risk {(m.risk_level * 100).toFixed(0)}%
              {m.sudden_brake && (
                <span className="ml-2 text-sentinel-danger">BRAKE ALERT</span>
              )}
            </li>
          ))
        )}
      </ul>
    </motion.section>
  )
}
