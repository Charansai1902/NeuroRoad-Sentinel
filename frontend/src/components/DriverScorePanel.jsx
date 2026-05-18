import { motion } from 'framer-motion'
import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip } from 'chart.js'

ChartJS.register(ArcElement, Tooltip)

export default function DriverScorePanel({ score }) {
  const overall = score?.overall ?? 0

  const chartData = {
    labels: ['Score', ''],
    datasets: [
      {
        data: [overall, 100 - overall],
        backgroundColor: ['#00d4aa', '#1e2a3a'],
        borderWidth: 0,
      },
    ],
  }

  const metrics = [
    { label: 'Safe Driving', value: score?.safe_driving },
    { label: 'Lane Discipline', value: score?.lane_discipline },
    { label: 'Speed Compliance', value: score?.speed_compliance },
    { label: 'Sudden Braking', value: score?.sudden_braking },
  ]

  return (
    <motion.section layout className="glass-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-sentinel-muted mb-3">
        Driver Behavior Score
      </h2>
      <div className="flex items-center gap-4">
        <div className="w-24 h-24">
          <Doughnut
            data={chartData}
            options={{
              cutout: '70%',
              plugins: { legend: { display: false }, tooltip: { enabled: false } },
            }}
          />
        </div>
        <div>
          <p className="text-3xl font-bold font-mono">{overall.toFixed(0)}</p>
          <p className="text-xs text-sentinel-muted">Overall / 100</p>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {metrics.map((m) => (
          <div key={m.label}>
            <motion.div className="flex justify-between text-xs mb-1">
              <span className="text-sentinel-muted">{m.label}</span>
              <span className="font-mono">{(m.value ?? 0).toFixed(0)}</span>
            </motion.div>
            <div className="h-1.5 rounded-full bg-sentinel-border overflow-hidden">
              <motion.div
                className="h-full bg-sentinel-accent rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${m.value ?? 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </motion.section>
  )
}
