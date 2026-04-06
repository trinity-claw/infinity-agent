import React, { useState } from 'react';
import agentLogo from '../../infinity-agent-logo.png';

const getFallbackUserId = () => 'client789';

const SUGGESTION_GROUPS = [
  {
    id: 'products',
    label: 'Produtos e taxas',
    description: 'Perguntas sobre solucoes, taxas e funcionalidades da InfinitePay.',
    items: [
      {
        title: 'Taxas da Maquininha Smart',
        description: 'Entenda as taxas de debito e credito para vendas presenciais.',
        message: 'Quais sao as taxas da Maquininha Smart para debito e credito?',
      },
      {
        title: 'Como funciona o InfiniteTap',
        description: 'Saiba como transformar seu celular em maquininha.',
        message: 'Como usar o InfiniteTap para receber pagamentos no celular?',
      },
      {
        title: 'Pix Parcelado',
        description: 'Tire duvidas sobre parcelamento via Pix.',
        message: 'Como funciona o Pix Parcelado da InfinitePay?',
      },
      {
        title: 'Link de Pagamento',
        description: 'Veja como cobrar clientes com link online.',
        message: 'Como funciona o Link de Pagamento da InfinitePay para vendas online?',
      },
    ],
  },
  {
    id: 'support',
    label: 'Suporte de conta',
    description: 'Diagnosticos de acesso, transferencias, saldo e historico.',
    items: [
      {
        title: 'Nao consigo acessar minha conta',
        description: 'Fluxo de suporte para login e recuperacao de acesso.',
        message: 'Nao consigo acessar minha conta. Pode me ajudar com os proximos passos?',
      },
      {
        title: 'Transferencia falhando',
        description: 'Investigacao para problemas em transferencias.',
        message: 'Por que nao estou conseguindo fazer transferencias agora?',
      },
      {
        title: 'Consultar saldo disponivel',
        description: 'Checagem rapida do saldo da conta.',
        message: 'Quero consultar meu saldo disponivel agora.',
      },
      {
        title: 'Historico de transacoes',
        description: 'Ultimas movimentacoes para conferencia.',
        message: 'Mostre meu historico recente de transacoes, por favor.',
      },
    ],
  },
  {
    id: 'escalation',
    label: 'Escalacao humana',
    description: 'Atalhos para transferir o atendimento para um humano.',
    items: [
      {
        title: 'Falar com atendente humano',
        description: 'Solicita atendimento humano imediato.',
        message: 'Quero falar com um atendente humano agora.',
      },
      {
        title: 'Problema urgente',
        description: 'Sinaliza urgencia para priorizacao do atendimento.',
        message: 'Estou com um problema urgente e preciso de suporte humano agora.',
      },
    ],
  },
  {
    id: 'general',
    label: 'Perguntas gerais',
    description: 'Exemplos de perguntas fora do escopo de produtos.',
    items: [
      {
        title: 'Ultimo jogo do Palmeiras',
        description: 'Exemplo de busca web para pergunta geral.',
        message: 'Quando foi o ultimo jogo do Palmeiras?',
      },
      {
        title: 'Noticias de Sao Paulo hoje',
        description: 'Exemplo de pergunta de atualidades.',
        message: 'Quais as principais noticias de Sao Paulo hoje?',
      },
    ],
  },
];

const Sidebar = ({ onClearChat, onQuickSuggestion, userProfile, onLogout }) => {
  const [userId, setUserId] = useState(localStorage.getItem('infinity_user_id') || getFallbackUserId());
  const [selectedSuggestionGroup, setSelectedSuggestionGroup] = useState(SUGGESTION_GROUPS[0].id);

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

  const activeSuggestionGroup =
    SUGGESTION_GROUPS.find((group) => group.id === selectedSuggestionGroup) || SUGGESTION_GROUPS[0];

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
            placeholder="Ex: client789"
          />
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Sugestoes guiadas</div>
        <div className="suggestions-toolbar">
          <label htmlFor="suggestionGroupSelect" className="suggestions-label">
            Categoria
          </label>
          <select
            id="suggestionGroupSelect"
            className="suggestions-select"
            value={selectedSuggestionGroup}
            onChange={(event) => setSelectedSuggestionGroup(event.target.value)}
          >
            {SUGGESTION_GROUPS.map((group) => (
              <option key={group.id} value={group.id}>
                {group.label}
              </option>
            ))}
          </select>
          <p className="suggestions-group-hint">{activeSuggestionGroup.description}</p>
        </div>
        <div className="quick-actions suggestion-cards">
          {activeSuggestionGroup.items.map((item) => (
            <button
              key={item.title}
              type="button"
              className="quick-btn suggestion-btn"
              onClick={() => onQuickSuggestion?.(item.message)}
            >
              <span className="suggestion-title">{item.title}</span>
              <span className="suggestion-desc">{item.description}</span>
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
