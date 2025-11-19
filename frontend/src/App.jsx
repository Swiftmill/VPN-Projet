import { useEffect, useState } from 'react'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import { getClients, getServerStatus } from './api'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [status, setStatus] = useState(null)
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchData = async (authToken) => {
    try {
      setLoading(true)
      const [statusData, clientsData] = await Promise.all([
        getServerStatus(authToken),
        getClients(authToken)
      ])
      setStatus(statusData)
      setClients(clientsData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (token) {
      fetchData(token)
    }
  }, [token])

  const handleLogin = (value) => {
    setToken(value)
    localStorage.setItem('token', value)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setStatus(null)
    setClients([])
  }

  if (!token) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <DashboardPage
      token={token}
      status={status}
      clients={clients}
      refresh={() => fetchData(token)}
      loading={loading}
      error={error}
      onLogout={handleLogout}
    />
  )
}

export default App
