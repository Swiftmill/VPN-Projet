const QRCodeModal = ({ image, onClose }) => {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Scan with WireGuard app</h3>
        <img src={`data:image/png;base64,${image}`} alt="WireGuard client QR" className="qr" />
        <button className="ghost" onClick={onClose}>Close</button>
      </div>
    </div>
  )
}

export default QRCodeModal
