import { motion } from 'framer-motion'

export default function LiveCameraFeed({ frame }) {
  const jpeg = frame?.camera_frame_jpeg
  const live = frame?.live_mode
  const fps = frame?.fps
  const trackCount = frame?.metadata?.track_count ?? frame?.detections?.length ?? 0
  const isVideo = frame?.metadata?.input_type === 'video'
  const inputName = frame?.metadata?.input_source ?? ''

  return (
    <motion.section layout className="glass-panel glow-accent p-4">
      <motion.div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-sentinel-muted">
          {isVideo ? 'Live Video Feed' : 'Live AI Camera'}
        </h2>
        <motion.div className="flex gap-2 text-xs font-mono flex-wrap">
          {isVideo && (
            <span className="px-2 py-0.5 rounded border border-sentinel-warn/50 text-sentinel-warn bg-sentinel-warn/10">
              REC ● {inputName}
            </span>
          )}
          <span
            className={`px-2 py-0.5 rounded border ${
              live
                ? 'border-sentinel-accent/50 text-sentinel-accent'
                : 'border-sentinel-muted/40 text-sentinel-muted'
            }`}
          >
            {live ? 'YOLO + DeepSORT' : 'STANDBY'}
          </span>
          {fps > 0 && <span className="text-sentinel-muted">{Number(fps).toFixed(1)} FPS</span>}
          <span className="text-sentinel-muted">{trackCount} tracks</span>
        </motion.div>
      </motion.div>

      <motion.div className="relative rounded-lg overflow-hidden border border-sentinel-border bg-sentinel-bg aspect-video">
        {jpeg ? (
          <img
            src={`data:image/jpeg;base64,${jpeg}`}
            alt="Live ADAS feed with AI overlays"
            className="w-full h-full object-contain bg-black"
          />
        ) : (
          <motion.div className="absolute inset-0 flex flex-col items-center justify-center text-sentinel-muted">
            <div className="w-12 h-12 border-2 border-sentinel-accent/30 border-t-sentinel-accent rounded-full animate-spin mb-4" />
            <p className="text-sm">Waiting for live inference…</p>
            <p className="text-xs mt-2 font-mono">bash scripts/start_video_demo.sh</p>
          </motion.div>
        )}

        {frame?.metadata?.collision_probability > 0.5 && (
          <motion.div className="absolute top-3 right-3 px-3 py-1.5 rounded-lg bg-sentinel-danger/90 text-white text-xs font-bold font-mono animate-pulse">
            RISK {(frame.metadata.collision_probability * 100).toFixed(0)}%
          </motion.div>
        )}
      </motion.div>

      {frame?.detections?.length > 0 && (
        <motion.div className="mt-3 flex flex-wrap gap-2">
          {frame.detections.slice(0, 8).map((d) => (
            <span
              key={`${d.track_id}-${d.class_name}`}
              className="text-xs font-mono px-2 py-1 rounded bg-sentinel-bg border border-sentinel-border"
            >
              {d.class_name} #{d.track_id}
              {d.distance_m != null && ` · ${d.distance_m.toFixed(1)}m`}
              {d.ttc_sec != null && ` · TTC ${d.ttc_sec.toFixed(1)}s`}
            </span>
          ))}
        </motion.div>
      )}
    </motion.section>
  )
}
