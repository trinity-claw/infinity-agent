import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import infinitePayLogo from '../logo.svg';

const ChatArea = ({ messages, typing, streamStatus, onSendMessage, userProfile, onToggleSidebar }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typing]);

  const getAgentBadge = (agent) => {
    const badges = {
      human: '<span class="agent-badge badge-human">Human</span>',
      support: '<span class="agent-badge badge-support">Support</span>',
      knowledge: '<span class="agent-badge badge-knowledge">Knowledge</span>',
      sentiment: '<span class="agent-badge badge-sentiment">Sentiment</span>',
      guardrail: '<span class="agent-badge badge-guardrail">Guardrail</span>',
      processing: '<span class="agent-badge badge-router">Processing</span>',
      unknown: '<span class="agent-badge badge-router">Agent</span>',
    };
    return badges[agent?.toLowerCase()] || '';
  };

  const firstName = userProfile?.name?.trim()?.split(' ')?.[0];

  const sendSuggestion = (message) => {
    if (typeof onSendMessage === 'function') {
      onSendMessage(message);
    }
  };

  return (
    <>
      <div className="chat-header">
        <div className="header-left">
          <button
            className="sidebar-toggle"
            id="sidebarToggle"
            aria-label="Menu"
            onClick={onToggleSidebar}
          >
            <svg viewBox="0 0 24 24" fill="none">
              <path stroke="currentColor" strokeWidth="2" strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="header-title">
            <h1>Infinity Agent</h1>
            <span className="header-subtitle">O assistente da Infinite Pay</span>
          </div>
        </div>
        <div className="header-right">
          <div className="header-brand-pill" title="InfinitePay">
            <img src={infinitePayLogo} alt="InfinitePay" className="header-brand-logo" />
          </div>
        </div>
      </div>

      <div id="messagesArea" className="messages-area">
        {messages.length === 0 && (
          <div className="welcome-screen">
            <div className="welcome-icon">
              <svg viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="30" stroke="#00E676" strokeWidth="2" opacity="0.3" />
                <circle cx="32" cy="32" r="22" stroke="#00E676" strokeWidth="1.5" opacity="0.5" />
                <path
                  d="M20 32C20 25.373 25.373 20 32 20C38.627 20 44 25.373 44 32C44 38.627 38.627 44 32 44C25.373 44 20 38.627 20 32Z"
                  fill="rgba(0,230,118,0.1)"
                  stroke="#00E676"
                  strokeWidth="2"
                />
                <path d="M26 32L30 36L38 27" stroke="#00E676" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2>{firstName ? `Olá, ${firstName}! Como posso ajudar?` : 'Olá! Como posso ajudar?'}</h2>
            <p>
              Sou o assistente de IA da InfinitePay. Posso responder perguntas sobre produtos, ajudar com sua conta ou
              buscar informações gerais.
            </p>
            <div className="welcome-chips">
              <button className="chip" type="button" onClick={() => sendSuggestion('Quais são os produtos da InfinitePay?')}>
                Produtos disponíveis
              </button>
              <button className="chip" type="button" onClick={() => sendSuggestion('Qual é a taxa do Pix na InfinitePay?')}>
                Taxa do Pix
              </button>
              <button className="chip" type="button" onClick={() => sendSuggestion('Como gerar um link de pagamento?')}>
                Link de Pagamento
              </button>
              <button className="chip" type="button" onClick={() => sendSuggestion('Quero falar com um atendente humano')}>
                Falar com Atendente
              </button>
            </div>
          </div>
        )}

        {messages.map((msg, index) => {
          const isUser = msg.sender === 'user';
          const roleClass = isUser ? 'user' : 'agent';

          return (
            <div key={msg.id || index} className={`message ${roleClass}`}>
              <div className="msg-avatar">
                {isUser ? (
                  'EU'
                ) : (
                  <svg viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <circle cx="12" cy="10" r="3" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path
                      d="M7 20.662V19A2 2 0 0 1 9 17H15A2 2 0 0 1 17 19V20.662"
                      stroke="#00E676"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>

              <div className="msg-body">
                <div className="msg-meta">
                  <span className="msg-time">
                    {new Date(msg.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {!isUser && msg.agent && <span dangerouslySetInnerHTML={{ __html: getAgentBadge(msg.agent) }} />}
                </div>

                <div className="msg-bubble">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>

                {msg.metadata?.escalated && (
                  <div className="escalation-notice">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                      />
                    </svg>
                    Aviso: Um atendente humano foi notificado e assumiu esta conversa. As próximas mensagens serão
                    encaminhadas para ele via WhatsApp (retorno assíncrono).
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {typing && (
          <div className="typing-indicator">
            <div className="typing-avatar">
              <svg viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <circle cx="12" cy="10" r="3" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path
                  d="M7 20.662V19A2 2 0 0 1 9 17H15A2 2 0 0 1 17 19V20.662"
                  stroke="#00E676"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            {streamStatus && <div className="typing-status">{streamStatus}</div>}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </>
  );
};

export default ChatArea;
