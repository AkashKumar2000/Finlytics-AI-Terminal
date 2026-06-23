export default function StreamingProgress({ events }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 font-mono text-sm space-y-1 max-h-64 overflow-y-auto">
      {events.map((ev, i) => (
        <div key={i} className={`flex gap-2 ${ev.type === 'error' ? 'text-red-400' : ev.type === 'tool' ? 'text-yellow-300' : ev.type === 'done' ? 'text-green-400' : 'text-gray-300'}`}>
          <span className="text-gray-500 text-xs mt-0.5 shrink-0">
            {new Date(ev.timestamp).toLocaleTimeString('en-IN', { hour12: false })}
          </span>
          <span>
            {ev.type === 'tool' && '🔧 '}
            {ev.type === 'done' && '✅ '}
            {ev.type === 'error' && '❌ '}
            {ev.message}
          </span>
        </div>
      ))}
      {events.length === 0 && (
        <p className="text-gray-500">Waiting for agent...</p>
      )}
    </div>
  )
}
