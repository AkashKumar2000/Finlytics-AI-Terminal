import { useNavigate } from 'react-router-dom'
import { formatDate } from '../../utils/formatters'

export default function WatchlistTable({ items, onRemove }) {
  const navigate = useNavigate()

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="text-left px-4 py-3 text-gray-500 font-medium">Symbol</th>
            <th className="text-left px-4 py-3 text-gray-500 font-medium">Company</th>
            <th className="text-left px-4 py-3 text-gray-500 font-medium">Notes</th>
            <th className="text-left px-4 py-3 text-gray-500 font-medium">Added</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => (
            <tr key={item.id} className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${i % 2 === 0 ? '' : 'bg-gray-50/30'}`}>
              <td className="px-4 py-3">
                <button
                  onClick={() => navigate(`/research/new?symbol=${item.symbol}`)}
                  className="font-mono font-bold text-blue-600 hover:text-blue-800 hover:underline"
                >
                  {item.symbol}
                </button>
              </td>
              <td className="px-4 py-3 text-gray-900">{item.company_name}</td>
              <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{item.notes || '—'}</td>
              <td className="px-4 py-3 text-gray-400 text-xs">{formatDate(item.created_at)}</td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => onRemove(item.id)}
                  className="text-xs text-red-500 hover:text-red-700 hover:underline"
                >
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
