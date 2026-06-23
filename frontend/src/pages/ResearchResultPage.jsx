import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Header from '../components/Layout/Header'
import ResultsRenderer from '../components/Research/ResultsRenderer'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorState from '../components/common/ErrorState'
import client from '../api/client'
import { formatDate } from '../utils/formatters'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export default function ResearchResultPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [exporting, setExporting] = useState(false)

  // Title editing
  const [editingTitle, setEditingTitle] = useState(false)
  const [newTitle, setNewTitle] = useState('')

  // Tag editing
  const [editingTags, setEditingTags] = useState(false)
  const [tagInput, setTagInput] = useState('')
  const [draftTags, setDraftTags] = useState([])

  const fetchReport = () => {
    setLoading(true)
    client.get(`/research/${id}`)
      .then((res) => {
        setReport(res.data)
        setNewTitle(res.data.title)
        setDraftTags(res.data.tags || [])
      })
      .catch(() => setError('Report not found or access denied'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchReport() }, [id])

  const handleDelete = async () => {
    if (!confirm('Delete this report?')) return
    setDeleting(true)
    try {
      await client.delete(`/research/${id}`)
      navigate('/research')
    } catch {
      alert('Delete failed')
      setDeleting(false)
    }
  }

  const handleUpdateTitle = async () => {
    if (!newTitle.trim() || newTitle === report.title) { setEditingTitle(false); return }
    try {
      const res = await client.put(`/research/${id}`, { title: newTitle })
      setReport(res.data)
      setEditingTitle(false)
    } catch { alert('Update failed') }
  }

  // Tag management
  const handleAddTag = () => {
    const tag = tagInput.trim()
    if (!tag || draftTags.includes(tag)) { setTagInput(''); return }
    setDraftTags((prev) => [...prev, tag])
    setTagInput('')
  }

  const handleRemoveTag = (tag) => {
    setDraftTags((prev) => prev.filter((t) => t !== tag))
  }

  const handleSaveTags = async () => {
    try {
      const res = await client.put(`/research/${id}`, { tags: draftTags })
      setReport(res.data)
      setEditingTags(false)
    } catch { alert('Failed to save tags') }
  }

  const handleCancelTags = () => {
    setDraftTags(report?.tags || [])
    setTagInput('')
    setEditingTags(false)
  }

  // PDF export
  const handleExportPDF = async () => {
    setExporting(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_BASE}/research/${id}/export`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) throw new Error('Export failed')
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${(report?.title || 'report').slice(0, 40).replace(/[^a-z0-9 _-]/gi, '_')}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      alert('PDF export failed')
    } finally {
      setExporting(false)
    }
  }

  if (loading) return (
    <div className="ml-60">
      <Header title="Research Report" />
      <div className="flex items-center justify-center h-96"><LoadingSpinner size="lg" /></div>
    </div>
  )

  if (error) return (
    <div className="ml-60">
      <Header title="Research Report" />
      <div className="p-6"><ErrorState message={error} onRetry={fetchReport} /></div>
    </div>
  )

  const resultData = report?.result_data || {}

  return (
    <div className="ml-60">
      <Header title="Research Report" subtitle={formatDate(report?.created_at)} />

      <main className="p-6 max-w-4xl">
        {/* Report meta bar */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
          {/* Title row */}
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex-1 min-w-0">
              {editingTitle ? (
                <div className="flex gap-2 items-center">
                  <input
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleUpdateTitle()}
                    className="flex-1 px-3 py-1.5 border border-blue-400 rounded-lg text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                  <button onClick={handleUpdateTitle} className="text-xs text-blue-600 font-medium hover:underline">Save</button>
                  <button onClick={() => setEditingTitle(false)} className="text-xs text-gray-400 hover:underline">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h2 className="font-bold text-gray-900 text-base">{report?.title}</h2>
                  <button onClick={() => setEditingTitle(true)} className="text-gray-400 hover:text-gray-600 text-xs" title="Edit title">✏️</button>
                </div>
              )}
              <p className="text-sm text-gray-500 mt-1 italic">"{report?.query}"</p>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 shrink-0">
              <button
                onClick={handleExportPDF}
                disabled={exporting}
                className="px-3 py-1.5 border border-gray-200 text-gray-600 rounded-lg text-xs font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors flex items-center gap-1"
              >
                {exporting ? 'Exporting...' : '↓ PDF'}
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-3 py-1.5 border border-red-200 text-red-600 rounded-lg text-xs font-medium hover:bg-red-50 disabled:opacity-50 transition-colors"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>

          {/* Tags row */}
          <div>
            {editingTags ? (
              <div className="space-y-2">
                {/* Existing tags with remove */}
                <div className="flex flex-wrap gap-2">
                  {draftTags.map((tag) => (
                    <span key={tag} className="flex items-center gap-1 px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 rounded-full text-xs font-medium">
                      {tag}
                      <button onClick={() => handleRemoveTag(tag)} className="text-blue-400 hover:text-red-500 ml-0.5 leading-none" title="Remove tag">×</button>
                    </span>
                  ))}
                  {draftTags.length === 0 && <span className="text-xs text-gray-400">No tags</span>}
                </div>
                {/* Add tag input */}
                <div className="flex gap-2 items-center">
                  <input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                    placeholder="Add tag..."
                    className="px-2 py-1 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 w-32"
                    autoFocus
                  />
                  <button onClick={handleAddTag} className="text-xs text-blue-600 font-medium hover:underline">Add</button>
                  <button onClick={handleSaveTags} className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700">Save</button>
                  <button onClick={handleCancelTags} className="text-xs text-gray-400 hover:underline">Cancel</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 flex-wrap">
                {report?.tags?.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 rounded-full text-xs font-medium">
                    {tag}
                  </span>
                ))}
                <button
                  onClick={() => { setDraftTags(report?.tags || []); setEditingTags(true) }}
                  className="text-xs text-gray-400 hover:text-gray-600 border border-dashed border-gray-300 px-2 py-0.5 rounded-full hover:border-gray-400 transition-colors"
                >
                  {report?.tags?.length ? 'Edit tags' : '+ Add tags'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Render AI results */}
        <ResultsRenderer report={resultData} />
      </main>
    </div>
  )
}
