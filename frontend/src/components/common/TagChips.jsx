const COLORS = [
  'bg-blue-100 text-blue-700',
  'bg-green-100 text-green-700',
  'bg-purple-100 text-purple-700',
  'bg-orange-100 text-orange-700',
  'bg-pink-100 text-pink-700',
]

export default function TagChips({ tags = [], onRemove }) {
  if (!tags.length) return null
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag, i) => (
        <span
          key={tag}
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${COLORS[i % COLORS.length]}`}
        >
          {tag}
          {onRemove && (
            <button onClick={() => onRemove(tag)} className="hover:opacity-70 ml-0.5">×</button>
          )}
        </span>
      ))}
    </div>
  )
}
