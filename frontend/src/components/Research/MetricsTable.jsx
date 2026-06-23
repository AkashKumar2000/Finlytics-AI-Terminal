import { formatPercent, formatNumber, formatPrice, formatINR } from '../../utils/formatters'

const METRIC_FORMATTERS = {
  current_price: formatPrice,
  market_cap: formatINR,
  revenue: formatINR,
  free_cash_flow: formatINR,
  eps: formatPrice,
  pe_ratio: (v) => formatNumber(v, 1) + 'x',
  forward_pe: (v) => formatNumber(v, 1) + 'x',
  profit_margin: formatPercent,
  operating_margin: formatPercent,
  return_on_equity: formatPercent,
  revenue_growth: formatPercent,
  dividend_yield: formatPercent,
  debt_to_equity: (v) => formatNumber(v, 2),
  beta: (v) => formatNumber(v, 2),
}

const METRIC_LABELS = {
  current_price: 'Current Price',
  market_cap: 'Market Cap',
  pe_ratio: 'Trailing P/E',
  forward_pe: 'Forward P/E',
  eps: 'EPS (TTM)',
  revenue: 'Revenue (TTM)',
  revenue_growth: 'Revenue Growth YoY',
  profit_margin: 'Net Profit Margin',
  operating_margin: 'Operating Margin',
  return_on_equity: 'Return on Equity',
  debt_to_equity: 'Debt / Equity',
  free_cash_flow: 'Free Cash Flow',
  dividend_yield: 'Dividend Yield',
  beta: 'Beta',
}

export default function MetricsTable({ data }) {
  if (!data) return null
  const entries = Object.entries(METRIC_LABELS)
    .filter(([key]) => data[key] != null)
    .map(([key, label]) => {
      const formatter = METRIC_FORMATTERS[key] || String
      return { label, value: formatter(data[key]) }
    })

  if (!entries.length) return <p className="text-sm text-gray-400">No metrics available.</p>

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="text-left px-4 py-3 text-gray-500 font-medium">Metric</th>
            <th className="text-right px-4 py-3 text-gray-500 font-medium">Value</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(({ label, value }, i) => (
            <tr key={label} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2.5 text-gray-600">{label}</td>
              <td className="px-4 py-2.5 text-right font-semibold text-gray-900">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
