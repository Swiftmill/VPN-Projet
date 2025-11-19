const ClientsTable = ({ clients, onDelete, onDownload, onShowQr }) => (
  <div className="card">
    <div className="card-header">
      <div>
        <h3>Clients</h3>
        <p>All issued WireGuard profiles.</p>
      </div>
    </div>
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>IP</th>
            <th>Public Key</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {clients.length === 0 && (
            <tr>
              <td colSpan="5" className="empty">No clients yet.</td>
            </tr>
          )}
          {clients.map((client) => (
            <tr key={client.id}>
              <td>{client.name}</td>
              <td>{client.ip_address}</td>
              <td className="mono">{client.public_key.slice(0, 24)}...</td>
              <td>{new Date(client.created_at).toLocaleString()}</td>
              <td className="actions">
                <button onClick={() => onDownload(client.id)}>Config</button>
                <button onClick={() => onShowQr(client.id)} className="ghost">QR</button>
                <button onClick={() => onDelete(client.id)} className="danger">Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
)

export default ClientsTable
