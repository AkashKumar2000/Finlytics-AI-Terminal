import { formatPrice, formatINR, formatPercent, formatNumber } from '../../utils/formatters'

export default function CompanyCard({ data }) {
  if (!data) return null
  const change = data.current_price && data.previous_close
    ? ((data.current_price - data.previous_close) / data.previous_close) * 100
    : null

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{data.company_name || data.symbol}</h3>
          <p className="text-sm text-gray-500">{data.symbol} · {data.exchange || 'NSE'} · {data.sector || 'N/A'}</p>
        </div>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
          {data.currency || 'INR'}
        </span>
      </div>

      <div className="flex items-end gap-3 mb-5">
        <span className="text-3xl font-bold text-gray-900">{formatPrice(data.current_price)}</span>
        {change != null && (
          <span className={`text-sm font-medium pb-1 ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        {[
          ['Market Cap', formatINR(data.market_cap)],
          ['P/E Ratio', formatNumber(data.pe_ratio)],
          ['EPS', formatPrice(data.eps)],
          ['Revenue', formatINR(data.revenue)],
          ['Profit Margin', formatPercent(data.profit_margin)],
          ['52W High', formatPrice(data['52_week_high'])],
          ['52W Low', formatPrice(data['52_week_low'])],
          ['Beta', formatNumber(data.beta)],
        ].map(([label, value]) => (
          <div key={label} className="bg-gray-50 rounded-lg p-2.5">
            <p className="text-xs text-gray-500 mb-0.5">{label}</p>
            <p className="font-semibold text-gray-900">{value}</p>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-400 mt-3">Source: {data.source || 'Zerodha Kite Connect'}</p>
    </div>
  )
}
