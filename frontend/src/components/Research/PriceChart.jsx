import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { formatPrice } from '../../utils/formatters'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
      <p className="text-gray-500 mb-1">{label}</p>
      <p className="font-bold text-gray-900">{formatPrice(payload[0].value)}</p>
    </div>
  )
}

export default function PriceChart({ data, symbol }) {
  if (!data?.prices?.length) return null

  const prices = data.prices.map((p) => ({
    date: p.date.slice(5),
    close: p.close,
  }))

  const min = Math.min(...prices.map((p) => p.close))
  const max = Math.max(...prices.map((p) => p.close))
  const isPositive = prices[prices.length - 1]?.close >= prices[0]?.close

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-900">{symbol} — Price History</h4>
        <span className="text-xs text-gray-400">{data.period} · {data.data_points} data points</span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={prices} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: '#9ca3af' }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[min * 0.98, max * 1.02]}
            tick={{ fontSize: 10, fill: '#9ca3af' }}
            tickLine={false}
            tickFormatter={(v) => `₹${v.toLocaleString('en-IN')}`}
            width={72}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="close"
            stroke={isPositive ? '#16a34a' : '#dc2626'}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-400 mt-2">Source: Yahoo Finance (NSE)</p>
    </div>
  )
}
