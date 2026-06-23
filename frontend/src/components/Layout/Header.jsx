import { useAuth } from '../../context/AuthContext'

export default function Header({ title, subtitle }) {
  const { user } = useAuth()
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium capitalize">{user?.role}</span>
        <span>{user?.full_name}</span>
      </div>
    </header>
  )
}
