import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Header from '../components/Layout/Header'
import QueryInput from '../components/Research/QueryInput'
import StreamingProgress from '../components/Research/StreamingProgress'
import client from '../api/client'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export default function NewResearchPage() {
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState([])
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const esRef = useRef(null)

  // Pre-fill query from watchlist click
  const prefillSymbol = searchParams.get('symbol')

  const handleSubmit = async (query) => {
    setLoading(true)
    setError('')
    setEvents([{ type: 'status', message: 'Starting research agent...', timestamp: new Date().toISOString() }])

    const token = localStorage.getItem('token')

    // Use SSE streaming endpoint
    const url = `${API_BASE}/research/query/stream`

    try {
      // First create the query via POST to get SSE stream
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let reportId = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              setEvents((prev) => [...prev, { ...data, timestamp: new Date().toISOString() }])

              if (data.type === 'done' && data.report_id) {
                reportId = data.report_id
              }
              if (data.type === 'error') {
                setError(data.message)
                setLoading(false)
                return
              }
            } catch {}
          }
        }
      }

      setLoading(false)
      if (reportId) {
        navigate(`/research/${reportId}`)
      } else {
        // Fallback: navigate to history
        navigate('/research')
      }

    } catch (err) {
      // Fallback to non-streaming if SSE fails
      try {
        setEvents((prev) => [...prev, { type: 'status', message: 'Switching to standard mode...', timestamp: new Date().toISOString() }])
        const res = await client.post('/research/query', { query })
        const reportId = res.data.id || res.data.report_id
        setLoading(false)
        if (reportId) navigate(`/research/${reportId}`)
        else navigate('/research')
      } catch (fallbackErr) {
        setError(fallbackErr.response?.data?.detail || 'Research query failed')
        setLoading(false)
      }
    }
  }

  useEffect(() => () => esRef.current?.close(), [])

  const initialQuery = prefillSymbol
    ? `Analyse ${prefillSymbol} — current price, financials, recent news, and key risks`
    : ''

  return (
    <div className="ml-60">
      <Header title="New Research" subtitle="Ask anything about Indian stocks (NSE / BSE)" />

      <main className="p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
              {error}
            </div>
          )}

          {!loading && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <QueryInput onSubmit={handleSubmit} loading={loading} initialQuery={initialQuery} />
            </div>
          )}

          {loading && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-blue-600" />
                <p className="font-medium text-gray-900">AI Agent is working...</p>
              </div>
              <StreamingProgress events={events} />
              <p className="text-xs text-gray-400">This may take 20–60 seconds. The agent is fetching market data, news, and document insights.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
