import { useState } from 'react'

const EXAMPLES = [
  'Analyse Reliance Industries Q4 FY26 earnings and key risks',
  'Compare TCS and Infosys on revenue growth and margins',
  'What is the outlook for HDFC Bank after the merger?',
  'Summarise Bharti Airtel concall highlights and 5G strategy',
]

export default function QueryInput({ onSubmit, loading }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) onSubmit(query.trim())
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything about Indian stocks — e.g. 'Analyse Reliance Q4 results and compare with TCS'"
          rows={4}
          disabled={loading}
          className="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit(e)
          }}
        />
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="mt-2 w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Running analysis...' : 'Run Research  ↵'}
        </button>
      </form>

      <div>
        <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Try an example</p>
        <div className="space-y-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setQuery(ex)}
              disabled={loading}
              className="block w-full text-left text-sm text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg px-3 py-2 transition-colors disabled:opacity-50"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
