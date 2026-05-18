import { motion, AnimatePresence } from 'framer-motion'

const LEVEL_STYLES = {
  critical: 'border-sentinel-danger/50 bg-sentinel-danger/10 text-sentinel-danger',
  warning: 'border-sentinel-warn/50 bg-sentinel-warn/10 text-sentinel-warn',
  info: 'border-sentinel-accent/30 bg-sentinel-accent/5 text-sentinel-accent',
}

export default function AlertPanel({ alerts }) {
  const list = alerts ?? []

  return (
    <motion.section layout className="glass-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-sentinel-muted mb-3">
        ADAS Decision Engine
      </h2>
      <AnimatePresence mode="popLayout">
        {list.length === 0 ? (
          <p className="text-sm text-sentinel-muted">No active alerts — road clear</p>
        ) : (
          <ul className="space-y-2">
            {list.map((a, i) => (
              <motion.li
                key={`${a.action}-${i}`}
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ opacity: 0 }}
                className={`rounded-lg border p-3 ${LEVEL_STYLES[a.level] || LEVEL_STYLES.info}`}
              >
                <p className="font-semibold text-sm text-white">{a.message}</p>
                <p className="text-xs mt-1 uppercase font-mono opacity-80">
                  {a.action.replace(/_/g, ' ')}
                </p>
                {a.explanation && (
                  <div className="mt-2 pt-2 border-t border-white/10">
                    <p className="text-xs text-sentinel-muted leading-relaxed">
                      <span className="text-white/70 font-medium">XAI: </span>
                      {a.explanation.summary}
                    </p>
                    {a.explanation.factors?.length > 0 && (
                      <ul className="mt-1 text-xs text-sentinel-muted list-disc list-inside">
                        {a.explanation.factors.map((f, j) => (
                          <li key={j}>{f}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </motion.li>
            ))}
          </ul>
        )}
      </AnimatePresence>
    </motion.section>
  )
}
