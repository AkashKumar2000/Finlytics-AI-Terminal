import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function SignupPage() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', mode: 'create', invite_code: '', org_name: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signup } = useAuth()
  const navigate = useNavigate()

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        ...(form.mode === 'create' ? { org_name: form.org_name } : { invite_code: form.invite_code }),
      }
      await signup(payload)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">📈</div>
          <h1 className="text-2xl font-bold text-gray-900">Investment Research</h1>
          <p className="text-gray-500 text-sm mt-1">Create your account</p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                value={form.full_name} onChange={(e) => set('full_name', e.target.value)}
                placeholder="Priya Sharma" required
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email" value={form.email} onChange={(e) => set('email', e.target.value)}
                placeholder="you@firm.com" required
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password" value={form.password} onChange={(e) => set('password', e.target.value)}
                placeholder="Min. 8 characters" required minLength={8}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Org mode toggle */}
            <div className="rounded-lg border border-gray-200 overflow-hidden">
              <div className="flex">
                {['create', 'join'].map((m) => (
                  <button
                    key={m} type="button" onClick={() => set('mode', m)}
                    className={`flex-1 py-2 text-sm font-medium transition-colors ${form.mode === m ? 'bg-blue-600 text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
                  >
                    {m === 'create' ? 'Create Organisation' : 'Join via Invite Code'}
                  </button>
                ))}
              </div>
              <div className="p-3">
                {form.mode === 'create' ? (
                  <input
                    value={form.org_name} onChange={(e) => set('org_name', e.target.value)}
                    placeholder="Organisation name (e.g. Alpha Capital)" required={form.mode === 'create'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <input
                    value={form.invite_code} onChange={(e) => set('invite_code', e.target.value)}
                    placeholder="Invite code (e.g. alpha123)" required={form.mode === 'join'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                )}
              </div>
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-600 hover:underline font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
