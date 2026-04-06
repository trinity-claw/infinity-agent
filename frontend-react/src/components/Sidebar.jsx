import React, { useEffect, useRef, useState } from 'react';
import agentLogo from '../../infinity-agent-logo.png';

const getFallbackUserId = () => 'client789';

const SUGGESTION_GROUPS = [
  {
    id: 'products',
    label: 'Produtos e taxas',
    description: 'Perguntas sobre soluções, taxas e funcionalidades da InfinitePay.',
    items: [
      {
        title: 'Taxas da Maquininha Smart',
        description: 'Entenda as taxas de débito e crédito para vendas presenciais.',
        message: 'Quais são as taxas da Maquininha Smart para débito e crédito?',
      },
      {
        title: 'Como funciona o InfiniteTap',
        description: 'Saiba como transformar seu celular em maquininha.',
        message: 'Como usar o InfiniteTap para receber pagamentos no celular?',
      },
      {
        title: 'Pix Parcelado',
        description: 'Tire dúvidas sobre parcelamento via Pix.',
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
    description: 'Diagnósticos de acesso, transferências, saldo e histórico.',
    items: [
      {
        title: 'Não consigo acessar minha conta',
        description: 'Fluxo de suporte para login e recuperação de acesso.',
        message: 'Não consigo acessar minha conta. Pode me ajudar com os próximos passos?',
      },
      {
        title: 'Transferência falhando',
        description: 'Investigação para problemas em transferências.',
        message: 'Por que não estou conseguindo fazer transferências agora?',
      },
      {
        title: 'Consultar saldo disponível',
        description: 'Checagem rápida do saldo da conta.',
        message: 'Quero consultar meu saldo disponível agora.',
      },
      {
        title: 'Histórico de transações',
        description: 'Últimas movimentações para conferência.',
        message: 'Mostre meu histórico recente de transações, por favor.',
      },
    ],
  },
  {
    id: 'escalation',
    label: 'Escalação humana',
    description: 'Atalhos para transferir o atendimento para um humano.',
    items: [
      {
        title: 'Falar com atendente humano',
        description: 'Solicita atendimento humano imediato.',
        message: 'Quero falar com um atendente humano agora.',
      },
      {
        title: 'Problema urgente',
        description: 'Sinaliza urgência para priorização do atendimento.',
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
        title: 'Último jogo do Palmeiras',
        description: 'Exemplo de busca web para pergunta geral.',
        message: 'Quando foi o último jogo do Palmeiras?',
      },
      {
        title: 'Notícias de São Paulo hoje',
        description: 'Exemplo de pergunta de atualidades.',
        message: 'Quais as principais notícias de São Paulo hoje?',
      },
    ],
  },
];

const Sidebar = ({ onClearChat, onQuickSuggestion, userProfile, onLogout }) => {
  const [userId, setUserId] = useState(localStorage.getItem('infinity_user_id') || getFallbackUserId());
  const [selectedSuggestionGroup, setSelectedSuggestionGroup] = useState(SUGGESTION_GROUPS[0].id);
  const [suggestionMenuOpen, setSuggestionMenuOpen] = useState(false);
  const suggestionDropdownRef = useRef(null);

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

  const handleSuggestionGroupSelect = (groupId) => {
    setSelectedSuggestionGroup(groupId);
    setSuggestionMenuOpen(false);
  };

  useEffect(() => {
    if (!suggestionMenuOpen) return undefined;

    const handleDocumentClick = (event) => {
      if (
        suggestionDropdownRef.current
        && !suggestionDropdownRef.current.contains(event.target)
      ) {
        setSuggestionMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleDocumentClick);
    return () => document.removeEventListener('mousedown', handleDocumentClick);
  }, [suggestionMenuOpen]);

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
              <span className="auth-session-name">{userProfile.name || 'Usuário autenticado'}</span>
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
        <div className="sidebar-label">Sugestões guiadas</div>
        <div className="suggestions-toolbar">
          <span className="suggestions-label">Categoria</span>
          <div className="suggestions-dropdown" ref={suggestionDropdownRef}>
            <button
              id="suggestionGroupSelect"
              type="button"
              className="suggestions-dropdown-trigger"
              aria-haspopup="listbox"
              aria-expanded={suggestionMenuOpen}
              onClick={() => setSuggestionMenuOpen((open) => !open)}
            >
              <span>{activeSuggestionGroup.label}</span>
              <span
                className={`suggestions-dropdown-icon ${suggestionMenuOpen ? 'open' : ''}`}
                aria-hidden="true"
              >
                ▾
              </span>
            </button>

            {suggestionMenuOpen && (
              <div className="suggestions-dropdown-menu" role="listbox" aria-label="Categorias de sugestões">
                {SUGGESTION_GROUPS.map((group) => {
                  const isActive = group.id === selectedSuggestionGroup;
                  return (
                    <button
                      key={group.id}
                      type="button"
                      role="option"
                      aria-selected={isActive}
                      className={`suggestions-dropdown-item ${isActive ? 'active' : ''}`}
                      onClick={() => handleSuggestionGroupSelect(group.id)}
                    >
                      {group.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
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
            Limpar Histórico Local
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
