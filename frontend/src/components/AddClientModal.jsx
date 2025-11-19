import { useState } from 'react'

const AddClientModal = ({ onClose, onCreate, loading }) => {
  const [name, setName] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onCreate({ name })
  }

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Create WireGuard Client</h3>
        <form onSubmit={handleSubmit}>
          <label>
            Device Name
            <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Jane's iPhone" />
          </label>
          <div className="modal-actions">
            <button type="button" className="ghost" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={loading}>{loading ? 'Creating...' : 'Create'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AddClientModal
