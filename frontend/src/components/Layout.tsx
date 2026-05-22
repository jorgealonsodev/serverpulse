import { Link, useNavigate, Outlet } from 'react-router-dom'
import { Server, Plus, LogOut } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

interface LayoutProps {
  children?: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <header className="border-b border-border bg-card px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Server className="w-6 h-6 text-accent" />
            <h1 className="text-lg font-semibold">ServerPulse</h1>
          </div>
          <nav className="flex items-center gap-4">
            <Link
              to="/"
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/servers/new"
              className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1"
            >
              <Plus className="w-4 h-4" />
              New Server
            </Link>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1"
              aria-label="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
            {user && (
              <span className="text-xs text-gray-500">{user.email}</span>
            )}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {children ?? <Outlet />}
      </main>
    </div>
  )
}
