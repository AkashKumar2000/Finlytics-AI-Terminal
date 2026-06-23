import { useState, useEffect } from 'react'
import Header from '../components/Layout/Header'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorState from '../components/common/ErrorState'
import client from '../api/client'

export default function SettingsPage() {
  const [org, setOrg] = useState(null)
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editMode, setEditMode] = useState(false)
  const [form, setForm] = useState({ name: '', description: '' })
  const [saving, setSaving] = useState(false)
  const [showInvite, setShowInvite] = useState(false)
  const [inviteCode, setInviteCode] = useState('')

  const fetchData = () => {
    setLoading(true)
    Promise.all([client.get('/org/'), client.get('/org/members')])
      .then(([o, m]) => {
        setOrg(o.data)
        setForm({ name: o.data.name, description: o.data.description || '' })
        setMembers(m.data)
      })
      .catch(() => setError('Failed to load organisation settings'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await client.put('/org/', form)
      setOrg(res.data)
      setEditMode(false)
    } catch { alert('Update failed') }
    finally { setSaving(false) }
  }

  const handleShowInvite = async () => {
    try {
      const res = await client.get('/org/invite-code')
      setInviteCode(res.data.invite_code)
      setShowInvite(true)
    } catch { alert('Could not retrieve invite code') }
  }

  if (loading) return (
    <div className="ml-60">
      <Header title="Settings" />
      <div className="flex items-center justify-center h-96"><LoadingSpinner size="lg" /></div>
    </div>
  )

  if (error) return (
    <div className="ml-60">
      <Header title="Settings" />
      <div className="p-6"><ErrorState message={error} onRetry={fetchData} /></div>
    </div>
  )

  return (
    <div className="ml-60">
      <Header title="Organisation Settings" subtitle="Admin only" />

      <main className="p-6 max-w-2xl space-y-5">
        {/* Org details */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Organisation</h3>
            {!editMode && (
              <button onClick={() => setEditMode(true)} className="text-sm text-blue-600 hover:underline">Edit</button>
            )}
          </div>

          {editMode ? (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>
              <div className="flex gap-2">
                <button onClick={handleSave} disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button onClick={() => setEditMode(false)} className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="flex gap-4"><span className="text-gray-500 w-28">Name</span><span className="font-medium text-gray-900">{org?.name}</span></div>
              <div className="flex gap-4"><span className="text-gray-500 w-28">Slug</span><span className="font-mono text-gray-600">{org?.slug}</span></div>
              <div className="flex gap-4"><span className="text-gray-500 w-28">Description</span><span className="text-gray-700">{org?.description || '—'}</span></div>
            </div>
          )}
        </div>

        {/* Invite code */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Invite Code</h3>
          <p className="text-sm text-gray-500 mb-3">Share this code with new analysts to let them join your organisation.</p>
          {showInvite ? (
            <div className="flex items-center gap-3">
              <code className="px-4 py-2 bg-gray-100 rounded-lg text-gray-900 font-mono font-bold text-lg tracking-widest">
                {inviteCode}
              </code>
              <button onClick={() => { navigator.clipboard.writeText(inviteCode) }} className="text-xs text-blue-600 hover:underline">Copy</button>
            </div>
          ) : (
            <button onClick={handleShowInvite} className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 font-medium">
              Show Invite Code
            </button>
          )}
        </div>

        {/* Members */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Members ({members.length})</h3>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Name</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Email</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Role</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m, i) => (
                <tr key={m.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-3 font-medium text-gray-900">{m.full_name}</td>
                  <td className="px-6 py-3 text-gray-500">{m.email}</td>
                  <td className="px-6 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${m.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                      {m.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
