const StatusCard = ({ status }) => (
  <div className="card">
    <div className="card-header">
      <div>
        <h3>Server Status</h3>
        <p>Interface {status?.interface || 'wg0'}</p>
      </div>
      <span className={`badge ${status?.is_running ? 'success' : 'danger'}`}>
        {status?.is_running ? 'Online' : 'Offline'}
      </span>
    </div>
    <div className="status-grid">
      <div>
        <span>Public Key</span>
        <p className="mono">{status?.public_key || 'N/A'}</p>
      </div>
      <div>
        <span>Listen Port</span>
        <p>{status?.listen_port || 'N/A'}</p>
      </div>
      <div>
        <span>Connected Peers</span>
        <p>{status?.peers_count ?? 0}</p>
      </div>
      <div>
        <span>Last Handshake</span>
        <p>{status?.latest_handshake || 'No activity yet'}</p>
      </div>
    </div>
  </div>
)

export default StatusCard
