import React, { useState } from 'react';
import logo from '../logo.svg';

const Sidebar = ({ onClearChat }) => {
  const [userId, setUserId] = useState(
    localStorage.getItem('infinity_user_id') || `client_${Math.floor(Math.random() * 10000)}`
  );

  const handleUserIdChange = (e) => {
    const newId = e.target.value;
    setUserId(newId);
    localStorage.setItem('infinity_user_id', newId);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo-pill">
          <img src={logo} alt="InfinitePay" className="logo-img" />
        </div>
        <div className="sidebar-header-right">
          <span className="badge-ai">AI SWARM</span>
        </div>
      </div>
      
      <div className="sidebar-section">
        <div className="sidebar-label">Mock Auth</div>
        <div className="user-id-wrapper">
          <label htmlFor="userIdInput">Telefone/ID:</label>
          <input 
            type="text" 
            id="userIdInput" 
            value={userId}
            onChange={handleUserIdChange}
            placeholder="Ex: 5511999999999" 
          />
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">System Actions</div>
        <div className="quick-actions">
          <button id="clearBtn" onClick={onClearChat} className="quick-btn">Limpar Histórico Local</button>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="status-row">
          <span className="status-dot online"></span>
          <span>System Online</span>
        </div>
        <div className="health-info">
          Infinity Agent v1.0 <br />
          LangGraph SQLite
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
