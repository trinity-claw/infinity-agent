import React, { useState } from 'react';
import agentLogo from '../../infinity-agent-logo.png';

const getFallbackUserId = () => `client_${Math.floor(Math.random() * 10000)}`;

const QUICK_SUGGESTIONS = [
  { label: 'Taxas da maquininha', message: 'Quais sao as taxas da Maquininha Smart?' },
  { label: 'Problema de acesso', message: 'Nao consigo acessar minha conta' },
  { label: 'Como usar InfiniteTap', message: 'Como usar o InfiniteTap?' },
  { label: 'Emprestimo empresarial', message: 'Quero fazer um emprestimo' },
  { label: 'Pix gratuito?', message: 'O Pix e gratuito na InfinitePay?' },
  { label: 'Falar com atendente', message: 'Quero falar com um atendente humano' },
  { label: 'Status dos servicos', message: 'Qual o status atual dos servicos da InfinitePay?' },
];

const Sidebar = ({ onClearChat, onQuickSuggestion, userProfile, onLogout }) => {
  const [userId, setUserId] = useState(localStorage.getItem('infinity_user_id') || getFallbackUserId());

  const handleUserIdChange = (event) => {
    const newId = event.target.value;
    setUserId(newId);
    localStorage.setItem('infinity_user_id', newId);
  };

  const initials = userProfile?.name
    ? userProfile.name
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0].toUpperCase())
        .join('')
    : 'IA';

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="agent-brand-card" title="Infinity Agent">
          <img src={agentLogo} alt="Infinity Agent" className="agent-brand-logo" />
          <div className="agent-brand-meta">
            <span className="agent-brand-title">Infinity Agent</span>
            <span className="agent-brand-subtitle">AI Swarm</span>
          </div>
        </div>
      </div>

      {userProfile && (
        <div className="sidebar-section">
          <div className="sidebar-label">Google Session</div>
          <div className="auth-session-card">
            <div className="auth-session-avatar">
              {userProfile.picture ? (
                <img src={userProfile.picture} alt={userProfile.name || 'Avatar'} />
              ) : (
                <span>{initials}</span>
              )}
            </div>
            <div className="auth-session-meta">
              <span className="auth-session-name">{userProfile.name || 'Usuario autenticado'}</span>
              <span className="auth-session-email">{userProfile.email}</span>
            </div>
          </div>
          <button type="button" onClick={onLogout} className="quick-btn quick-btn-ghost">
            Sair da conta Google
          </button>
        </div>
      )}

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
        <div className="sidebar-label">Sugestoes rapidas</div>
        <div className="quick-actions">
          {QUICK_SUGGESTIONS.map((item) => (
            <button
              key={item.label}
              type="button"
              className="quick-btn"
              onClick={() => onQuickSuggestion?.(item.message)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">System Actions</div>
        <div className="quick-actions">
          <button type="button" id="clearBtn" onClick={onClearChat} className="quick-btn">
            Limpar Historico Local
          </button>
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
    </aside>
  );
};

export default Sidebar;
