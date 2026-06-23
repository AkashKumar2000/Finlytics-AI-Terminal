import { useState, useEffect } from 'react'
import Header from '../components/Layout/Header'
import WatchlistTable from '../components/Watchlist/WatchlistTable'
import AddCompanyForm from '../components/Watchlist/AddCompanyForm'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import client from '../api/client'

export default function WatchlistPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchWatchlist = () => {
    setLoading(true)
    client.get('/watchlist/')
      .then((res) => setItems(res.data))
      .catch(() => setError('Failed to load watchlist'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchWatchlist() }, [])

  const handleAdd = async (payload) => {
    const res = await client.post('/watchlist/', payload)
    setItems((prev) => [res.data, ...prev])
  }

  const handleRemove = async (id) => {
    if (!confirm('Remove from watchlist?')) return
    await client.delete(`/watchlist/${id}`)
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  return (
    <div className="ml-60">
      <Header title="Watchlist" subtitle={`${items.length} companies tracked`} />

      <main className="p-6 space-y-5">
        <AddCompanyForm onAdd={handleAdd} />

        {loading && <div className="py-16 flex justify-center"><LoadingSpinner /></div>}
        {error && <ErrorState message={error} onRetry={fetchWatchlist} />}

        {!loading && !error && items.length === 0 && (
          <EmptyState
            icon="⭐"
            title="No companies on watchlist"
            description="Add Indian stocks using NSE symbols (e.g. RELIANCE.NS, TCS.NS)"
          />
        )}

        {!loading && items.length > 0 && (
          <WatchlistTable items={items} onRemove={handleRemove} />
        )}
      </main>
    </div>
  )
}
