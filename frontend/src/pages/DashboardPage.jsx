import { useState } from 'react'
import { createClient, deleteClient, downloadConfig, getClientQr } from '../api'
import StatusCard from '../components/StatusCard'
import ClientsTable from '../components/ClientsTable'
import AddClientModal from '../components/AddClientModal'
import QRCodeModal from '../components/QRCodeModal'

const DashboardPage = ({ token, status, clients, refresh, loading, error, onLogout }) => {
  const [showAddModal, setShowAddModal] = useState(false)
  const [showQr, setShowQr] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const handleCreate = async (payload) => {
    setActionLoading(true)
    try {
      await createClient(token, payload)
      setShowAddModal(false)
      await refresh()
    } catch (err) {
      alert(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this client?')) return
    setActionLoading(true)
    try {
      await deleteClient(token, id)
      await refresh()
    } catch (err) {
      alert(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDownload = async (id) => {
    try {
      const data = await downloadConfig(token, id)
      const blob = new Blob([data.config], { type: 'text/plain' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `wireguard-client-${id}.conf`
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleQr = async (id) => {
    try {
      const data = await getClientQr(token, id)
      setShowQr(data.qrcode)
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="layout">
      <aside>
        <h2>WireGuard VPN</h2>
        <p>Private, self-hosted VPN control panel.</p>
        <button onClick={() => setShowAddModal(true)}>+ Add Client</button>
        <button className="ghost" onClick={refresh}>{loading ? 'Refreshing...' : 'Refresh'}</button>
        <button className="danger" onClick={onLogout}>Log out</button>
      </aside>
      <main>
        {error && <div className="error">{error}</div>}
        <StatusCard status={status} />
        <ClientsTable clients={clients} onDelete={handleDelete} onDownload={handleDownload} onShowQr={handleQr} />
      </main>

      {showAddModal && (
        <AddClientModal onClose={() => setShowAddModal(false)} onCreate={handleCreate} loading={actionLoading} />
      )}

      {showQr && <QRCodeModal image={showQr} onClose={() => setShowQr(null)} />}
    </div>
  )
}

export default DashboardPage
