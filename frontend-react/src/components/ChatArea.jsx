import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

const ChatArea = ({ messages, typing }) => {
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
      guardrail: '<span class="agent-badge badge-guardrail">Guardrail</span>'
    };
    return badges[agent?.toLowerCase()] || '';
  };

  return (
    <>
      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <button className="sidebar-toggle" id="sidebarToggle" aria-label="Menu" onClick={() => document.querySelector('.app-wrapper').classList.toggle('sidebar-collapsed')}>
            <svg viewBox="0 0 24 24" fill="none">
              <path stroke="currentColor" strokeWidth="2" strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <div className="header-title">
            <h1>Infinity Agent</h1>
            <span className="header-subtitle">Powered by LangGraph & GPT-4</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div id="messagesArea" className="messages-area">
        {messages.map((msg, index) => {
          const isUser = msg.sender === 'user';
          const isAssumedAgent = msg.sender === 'bot' || msg.sender === 'agent' || !isUser;
          const roleClass = isUser ? 'user' : 'agent';
          
          return (
            <div key={index} className={`message ${roleClass}`}>
              <div className="msg-avatar">
                {isUser ? 'EU' : (
                   <svg viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="10" r="3" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M7 20.662V19A2 2 0 0 1 9 17H15A2 2 0 0 1 17 19V20.662" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                   </svg>
                )}
              </div>
              <div className="msg-body">
                <div className="msg-meta">
                  <span className="msg-time">{new Date(msg.timestamp || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  {!isUser && msg.agent && (
                    <span dangerouslySetInnerHTML={{ __html: getAgentBadge(msg.agent) }} />
                  )}
                </div>
                <div className="msg-bubble">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
                {msg.metadata && msg.metadata.escalated && (
                  <div className="escalation-notice">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                    Aviso: Um atendente humano foi notificado e assumiu esta conversa. As próximas mensagens serão encaminhadas para ele via WhatsApp.
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
                  <circle cx="12" cy="12" r="10" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="12" cy="10" r="3" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M7 20.662V19A2 2 0 0 1 9 17H15A2 2 0 0 1 17 19V20.662" stroke="#00E676" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="typing-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </>
  );
};

export default ChatArea;
