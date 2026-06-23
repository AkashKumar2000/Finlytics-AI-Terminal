export function formatINR(value) {
  if (value == null) return 'N/A'
  const num = Number(value)
  if (isNaN(num)) return 'N/A'
  if (num >= 1e13) return `₹${(num / 1e13).toFixed(2)} Lakh Cr`
  if (num >= 1e11) return `₹${(num / 1e7).toFixed(0)} Cr`
  if (num >= 1e7)  return `₹${(num / 1e7).toFixed(2)} Cr`
  if (num >= 1e5)  return `₹${(num / 1e5).toFixed(2)} L`
  return `₹${num.toLocaleString('en-IN')}`
}

export function formatNumber(value, decimals = 2) {
  if (value == null) return 'N/A'
  const num = Number(value)
  if (isNaN(num)) return 'N/A'
  return num.toFixed(decimals)
}

export function formatPercent(value) {
  if (value == null) return 'N/A'
  return `${(Number(value) * 100).toFixed(2)}%`
}

export function formatDate(iso) {
  if (!iso) return 'N/A'
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

export function formatPrice(value) {
  if (value == null) return 'N/A'
  const num = Number(value)
  if (isNaN(num)) return 'N/A'
  return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
