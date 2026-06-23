import { formatPrice, formatINR, formatPercent, formatNumber } from '../../utils/formatters'

const FIELDS = [
  { key: 'current_price',   label: 'Price',          fmt: formatPrice },
  { key: 'market_cap',      label: 'Market Cap',     fmt: formatINR },
  { key: 'pe_ratio',        label: 'P/E',            fmt: (v) => formatNumber(v, 1) + 'x' },
  { key: 'eps',             label: 'EPS',            fmt: formatPrice },
  { key: 'revenue',         label: 'Revenue',        fmt: formatINR },
  { key: 'revenue_growth',  label: 'Rev Growth',     fmt: formatPercent },
  { key: 'profit_margin',   label: 'Net Margin',     fmt: formatPercent },
  { key: 'return_on_equity',label: 'ROE',            fmt: formatPercent },
  { key: 'debt_to_equity',  label: 'D/E',            fmt: (v) => formatNumber(v, 2) },
  { key: 'beta',            label: 'Beta',           fmt: (v) => formatNumber(v, 2) },
]

export default function ComparisonTable({ data }) {
  if (!data?.comparison?.length) return null
  const companies = data.comparison

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="text-left px-4 py-3 text-gray-500 font-medium">Metric</th>
            {companies.map((c) => (
              <th key={c.symbol} className="text-right px-4 py-3 text-gray-900 font-semibold">
                <div>{c.symbol.replace('.NS','').replace('.BO','')}</div>
                <div className="text-xs text-gray-400 font-normal">{c.company_name?.split(' ').slice(0,2).join(' ')}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {FIELDS.filter((f) => companies.some((c) => c[f.key] != null)).map((field, i) => (
            <tr key={field.key} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2.5 text-gray-600">{field.label}</td>
              {companies.map((c) => (
                <td key={c.symbol} className="px-4 py-2.5 text-right font-semibold text-gray-900">
                  {c[field.key] != null ? field.fmt(c[field.key]) : '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-gray-400 px-4 py-2 border-t border-gray-100">Source: Yahoo Finance</p>
    </div>
  )
}
