import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Layout/Header'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import TagChips from '../components/common/TagChips'
import client from '../api/client'
import { formatDate } from '../utils/formatters'

export default function ResearchHistoryPage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const navigate = useNavigate()
  const PAGE_SIZE = 10

  const fetchReports = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams({ limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE })
    if (search) params.set('search', search)

    client.get(`/research/?${params}`)
      .then((res) => {
        const data = res.data
        setReports(Array.isArray(data) ? data : data.reports || [])
        setTotal(data.total || (Array.isArray(data) ? data.length : 0))
      })
      .catch(() => setError('Failed to load reports'))
      .finally(() => setLoading(false))
  }, [page, search])

  useEffect(() => { fetchReports() }, [fetchReports])

  const handleSearch = (e) => {
    setSearch(e.target.value)
    setPage(1)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="ml-60">
      <Header title="Research History" subtitle={`${total} reports in your organisation`} />

      <main className="p-6 space-y-4">
        {/* Search */}
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
          <input
            value={search}
            onChange={handleSearch}
            placeholder="Search reports by title or query..."
            className="w-full pl-9 pr-4 py-2.5 bg-white border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex justify-end">
          <button
            onClick={() => navigate('/research/new')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            + New Research
          </button>
        </div>

        {loading && <div className="py-16 flex justify-center"><LoadingSpinner /></div>}
        {error && <ErrorState message={error} onRetry={fetchReports} />}

        {!loading && !error && reports.length === 0 && (
          <EmptyState
            icon="📭"
            title="No research reports yet"
            description="Start your first research query to see reports here."
            action={
              <button onClick={() => navigate('/research/new')} className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                New Research
              </button>
            }
          />
        )}

        {!loading && reports.length > 0 && (
          <div className="space-y-2">
            {reports.map((r) => (
              <button
                key={r.id}
                onClick={() => navigate(`/research/${r.id}`)}
                className="w-full text-left bg-white rounded-xl border border-gray-200 px-5 py-4 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-gray-900 truncate">{r.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">"{r.query}"</p>
                    {r.tags?.length > 0 && <div className="mt-2"><TagChips tags={r.tags} /></div>}
                  </div>
                  <div className="text-right shrink-0">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${r.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {r.status}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">{formatDate(r.created_at)}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40"
            >
              ← Prev
            </button>
            <span className="text-sm text-gray-600">Page {page} of {totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
