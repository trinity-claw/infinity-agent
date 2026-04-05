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
      <div className="logo-container">
        <img src={logo} alt="InfinitePay" />
      </div>
      
      <div className="user-settings">
        <label htmlFor="userIdInput">ID do Usuário / Telefone</label>
        <input 
          type="text" 
          id="userIdInput" 
          value={userId}
          onChange={handleUserIdChange}
          placeholder="Ex: 5511999999999" 
        />
        <small>Útil para testar a ponte do WhatsApp (escalonamento)</small>
      </div>

      <div className="action-buttons">
        <button id="clearBtn" onClick={onClearChat} className="secondary-btn">Limpar Histórico</button>
      </div>

      <div className="sidebar-footer">
        <p>Infinity Agent v1.0</p>
        <p className="status-indicator"><span className="dot"></span> Online</p>
      </div>
    </div>
  );
};

export default Sidebar;
