import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ServerNewPage from './pages/ServerNewPage'
import ServerDetailPage from './pages/ServerDetailPage'
import { AuthGuard } from './hooks/useAuth'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <AuthGuard>
            <DashboardPage />
          </AuthGuard>
        }
      />
      <Route
        path="/servers/new"
        element={
          <AuthGuard>
            <ServerNewPage />
          </AuthGuard>
        }
      />
      <Route
        path="/servers/:id"
        element={
          <AuthGuard>
            <ServerDetailPage />
          </AuthGuard>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
