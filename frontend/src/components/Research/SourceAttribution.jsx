const TYPE_STYLES = {
  market_data: 'bg-blue-50 text-blue-700 border-blue-200',
  news:        'bg-purple-50 text-purple-700 border-purple-200',
  document:    'bg-amber-50 text-amber-700 border-amber-200',
}
const TYPE_ICONS = { market_data: '📊', news: '📰', document: '📄' }

export default function SourceAttribution({ sources = [] }) {
  if (!sources.length) return null
  return (
    <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-3">Data Sources</h4>
      <div className="flex flex-wrap gap-2">
        {sources.map((s, i) => {
          const style = TYPE_STYLES[s.type] || 'bg-gray-100 text-gray-600 border-gray-200'
          const icon = TYPE_ICONS[s.type] || '🔗'
          return (
            <div key={i} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium ${style}`}>
              <span>{icon}</span>
              <div>
                <span className="font-semibold">{s.source}</span>
                {s.detail && <span className="opacity-75"> — {s.detail}</span>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
