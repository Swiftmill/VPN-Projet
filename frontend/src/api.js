const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const request = async (path, options = {}) => {
  const token = options.token
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  })

  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Request failed')
  }

  if (res.status === 204) {
    return null
  }

  return res.json()
}

export const login = async (username, password) => {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
}

export const getServerStatus = (token) => request('/server/status', { token })
export const getClients = (token) => request('/clients', { token })
export const createClient = (token, payload) => request('/clients', { method: 'POST', body: JSON.stringify(payload), token })
export const deleteClient = (token, id) => request(`/clients/${id}`, { method: 'DELETE', token })
export const downloadConfig = (token, id) => request(`/clients/${id}/config`, { token })
export const getClientQr = (token, id) => request(`/clients/${id}/qrcode`, { token })
