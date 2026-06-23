import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Layout/Header'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorState from '../components/common/ErrorState'
import TagChips from '../components/common/TagChips'
import client from '../api/client'
import { formatDate } from '../utils/formatters'

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [reports, setReports] = useState([])
  const [watchlist, setWatchlist] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      client.get('/research/?limit=5'),
      client.get('/watchlist/'),
    ])
      .then(([r, w]) => {
        setReports(r.data.reports || r.data)
        setWatchlist(w.data)
      })
      .catch(() => setError('Failed to load dashboard data'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="ml-60">
      <Header title="Dashboard" />
      <div className="flex items-center justify-center h-96"><LoadingSpinner size="lg" /></div>
    </div>
  )

  return (
    <div className="ml-60">
      <Header
        title={`Welcome back, ${user?.full_name?.split(' ')[0]} 👋`}
        subtitle={user?.org_name}
      />

      <main className="p-6 space-y-6">
        {error && <ErrorState message={error} onRetry={() => window.location.reload()} />}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Total Reports', value: reports.length, icon: '📋', color: 'bg-blue-50 border-blue-200' },
            { label: 'Watchlist', value: watchlist.length, icon: '⭐', color: 'bg-amber-50 border-amber-200' },
            { label: 'Organisation', value: user?.org_name?.split(' ').slice(0, 2).join(' '), icon: '🏢', color: 'bg-green-50 border-green-200' },
          ].map(({ label, value, icon, color }) => (
            <div key={label} className={`rounded-xl border p-5 ${color}`}>
              <div className="text-2xl mb-2">{icon}</div>
              <div className="text-2xl font-bold text-gray-900">{value}</div>
              <div className="text-sm text-gray-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'New Research', desc: 'Ask anything about Indian stocks', icon: '🔍', to: '/research/new', primary: true },
            { label: 'View History', desc: 'Browse past research reports', icon: '📋', to: '/research' },
            { label: 'Watchlist', desc: 'Manage tracked companies', icon: '⭐', to: '/watchlist' },
          ].map(({ label, desc, icon, to, primary }) => (
            <button
              key={label}
              onClick={() => navigate(to)}
              className={`text-left rounded-xl border p-4 transition-all hover:shadow-md ${primary ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-gray-200 hover:border-blue-300'}`}
            >
              <div className="text-xl mb-2">{icon}</div>
              <div className={`font-semibold text-sm ${primary ? 'text-white' : 'text-gray-900'}`}>{label}</div>
              <div className={`text-xs mt-0.5 ${primary ? 'text-blue-100' : 'text-gray-500'}`}>{desc}</div>
            </button>
          ))}
        </div>

        {/* Recent reports */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-900">Recent Research</h2>
            <button onClick={() => navigate('/research')} className="text-sm text-blue-600 hover:underline">View all →</button>
          </div>
          {reports.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center">
              <div className="text-4xl mb-3">📭</div>
              <p className="text-gray-500 text-sm">No research yet — start your first query!</p>
              <button onClick={() => navigate('/research/new')} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                New Research
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {reports.slice(0, 5).map((r) => (
                <button
                  key={r.id}
                  onClick={() => navigate(`/research/${r.id}`)}
                  className="w-full text-left bg-white rounded-xl border border-gray-200 px-5 py-4 hover:border-blue-300 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900 truncate">{r.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5 truncate">{r.query}</p>
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
        </div>
      </main>
    </div>
  )
}
