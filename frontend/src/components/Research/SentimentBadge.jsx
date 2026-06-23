const STYLES = {
  positive: 'bg-green-100 text-green-700 border border-green-200',
  negative: 'bg-red-100 text-red-700 border border-red-200',
  neutral:  'bg-gray-100 text-gray-600 border border-gray-200',
}
const ICONS = { positive: '↑', negative: '↓', neutral: '→' }

export default function SentimentBadge({ label }) {
  const key = label?.toLowerCase() || 'neutral'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${STYLES[key] || STYLES.neutral}`}>
      {ICONS[key]} {key.charAt(0).toUpperCase() + key.slice(1)}
    </span>
  )
}
