import { motion } from 'framer-motion'
import { useSentinelStream } from '../hooks/useWebSocket'
import AlertPanel from './AlertPanel'
import DigitalTwin from './DigitalTwin'
import LiveCameraFeed from './LiveCameraFeed'
import DriverScorePanel from './DriverScorePanel'
import RiskHeatmap from './RiskHeatmap'
import TelemetryCards from './TelemetryCards'
import V2VPanel from './V2VPanel'

export default function Dashboard() {
  const { frame, connected, error } = useSentinelStream()

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen p-4 md:p-6 font-display"
    >
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <motion.div layout>
          <p className="text-sentinel-accent text-xs font-mono uppercase tracking-widest">
            Cooperative ADAS
          </p>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            NeuroRoad <span className="text-sentinel-accent">Sentinel</span>
          </h1>
          <p className="text-sentinel-muted text-sm mt-1">
            Live YOLOv8 · DeepSORT · Real-time collision intelligence
          </p>
        </motion.div>
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono border ${
              connected
                ? 'border-sentinel-accent/40 text-sentinel-accent bg-sentinel-accent/10'
                : 'border-sentinel-danger/40 text-sentinel-danger bg-sentinel-danger/10'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${connected ? 'bg-sentinel-accent animate-pulse' : 'bg-sentinel-danger'}`}
            />
            {connected ? (frame?.live_mode ? 'LIVE AI' : 'LIVE') : 'RECONNECTING'}
          </span>
          {frame && (
            <span className="text-sentinel-muted text-xs font-mono">
              Frame #{frame.frame_id}
            </span>
          )}
        </div>
      </header>

      {error && (
        <p className="mb-4 text-sentinel-warn text-sm">
          {error} — start backend: <code className="font-mono">uvicorn main:app --reload</code>
        </p>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <motion.div className="xl:col-span-8 space-y-4">
          <LiveCameraFeed frame={frame} />
          <DigitalTwin frame={frame} />
          <RiskHeatmap heatmap={frame?.risk_heatmap} trajectories={frame?.trajectories} />
        </motion.div>
        <div className="xl:col-span-4 space-y-4">
          <TelemetryCards sensors={frame?.sensors} metadata={frame?.metadata} />
          <AlertPanel alerts={frame?.alerts} />
          <DriverScorePanel score={frame?.driver_score} />
          <V2VPanel messages={frame?.v2v_messages} />
        </div>
      </div>
    </motion.div>
  )
}
