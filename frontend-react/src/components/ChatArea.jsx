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
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h2>Infinity Agent</h2>
        <span className="subtitle">Powered by LangGraph & GPT-4</span>
      </div>

      {/* Messages */}
      <div id="chatBox" className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}-message`}>
            {msg.sender === 'bot' && (
              <div 
                className="agent-info" 
                dangerouslySetInnerHTML={{ __html: getAgentBadge(msg.agent) }} 
              />
            )}
            <div className="message-content">
               <ReactMarkdown>{msg.text}</ReactMarkdown>
            </div>
            {msg.metadata && msg.metadata.escalated && (
              <div className="escalation-alert">
                Aviso: Um atendente humano foi notificado e assumiu esta conversa.
                As próximas mensagens serão encaminhadas para ele via WhatsApp.
              </div>
            )}
            <div className="message-time">
              {new Date(msg.timestamp || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </div>
          </div>
        ))}

        {typing && (
          <div className="message bot-message">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatArea;
