import { motion } from 'framer-motion'

function Card({ label, value, unit }) {
  return (
    <div className="rounded-lg bg-sentinel-bg/60 border border-sentinel-border p-3">
      <p className="text-xs text-sentinel-muted uppercase tracking-wide">{label}</p>
      <p className="text-lg font-mono font-semibold mt-1">
        {value}
        {unit && <span className="text-sentinel-muted text-sm ml-1">{unit}</span>}
      </p>
    </div>
  )
}

export default function TelemetryCards({ sensors, metadata }) {
  const s = sensors ?? {}

  return (
    <motion.section layout className="glass-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-sentinel-muted mb-3">
        Sensor Fusion Telemetry
      </h2>
      <div className="grid grid-cols-2 gap-2">
        <Card label="Speed" value={s.speed_kmh?.toFixed?.(0) ?? '—'} unit="km/h" />
        <Card label="Heading" value={s.heading_deg?.toFixed?.(0) ?? '—'} unit="°" />
        <Card label="Front Radar" value={s.radar_front_m?.toFixed?.(1) ?? '—'} unit="m" />
        <Card label="Rear Radar" value={s.radar_rear_m?.toFixed?.(1) ?? '—'} unit="m" />
        <Card label="Left" value={s.radar_left_m?.toFixed?.(1) ?? '—'} unit="m" />
        <Card label="Right" value={s.radar_right_m?.toFixed?.(1) ?? '—'} unit="m" />
      </div>
      <p className="text-xs font-mono text-sentinel-muted mt-3 truncate">
        GPS {s.gps_lat?.toFixed(5)}, {s.gps_lon?.toFixed(5)}
      </p>
    </motion.section>
  )
}
