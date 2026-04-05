import React, { useState, useEffect, useRef } from 'react';
import WebGLBackground from './components/WebGLBackground';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';

function App() {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('infinity_chat_history');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { return [{ sender: 'bot', text: 'Olá! Sou o assistente de IA da InfinitePay. Como posso ajudar com seus negócios hoje?', agent: '' }]; }
    }
    return [
      { sender: 'bot', text: 'Olá! Sou o assistente de IA da InfinitePay. Como posso ajudar com seus negócios hoje?', agent: '' }
    ];
  });
  
  const [isTyping, setIsTyping] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  
  // Persist messages
  useEffect(() => {
    localStorage.setItem('infinity_chat_history', JSON.stringify(messages));
  }, [messages]);

  // Polling for WhatsApp replies if in escalation
  useEffect(() => {
    let pollingInterval;
    if (activeSessionId) {
      pollingInterval = setInterval(async () => {
        try {
          const response = await fetch(`/v1/escalation/whatsapp/messages/${activeSessionId}`);
          if (response.ok) {
            const data = await response.json();
            if (data.messages && data.messages.length > 0) {
              setMessages(prev => {
                const newMessages = [...prev];
                let added = false;
                for (const m of data.messages) {
                  // Only add message if we don't already have it
                  const exists = newMessages.some(x => x.id === m.id);
                  if (!exists) {
                    newMessages.push({
                      id: m.id,
                      sender: m.sender === 'user' ? 'user' : 'bot',
                      text: m.content,
                      agent: m.sender === 'human' ? 'human' : 'bot',
                      timestamp: m.timestamp
                    });
                    added = true;
                  }
                }
                return added ? newMessages : prev;
              });
            }
          } else if (response.status === 404) {
            setActiveSessionId(null); // Session closed
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 3000);
    }
    return () => clearInterval(pollingInterval);
  }, [activeSessionId]);

  const handleSendMessage = async (text) => {
    // Add user message
    const userMsg = { sender: 'user', text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const userId = localStorage.getItem('infinity_user_id') || 'client_web';
      const payload = {
        message: text,
        user_id: userId
      };

      if (activeSessionId) {
        payload.session_id = activeSessionId;
      }

      const response = await fetch('/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Falha na comunicação com a API');
      
      const data = await response.json();
      
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: data.response,
        agent: data.agent_used,
        metadata: data.metadata,
        timestamp: data.timestamp
      }]);

      if (data.metadata?.escalated && data.metadata?.session_id) {
        setActiveSessionId(data.metadata.session_id);
      }

    } catch (error) {
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'Desculpe, ocorreu um erro de conexão. Tente novamente.',
        agent: 'error'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleClearChat = () => {
    if (confirm('Tem certeza que deseja apagar todo o histórico?')) {
        setMessages([{ sender: 'bot', text: 'Olá! Sou o assistente de IA da InfinitePay. Como posso ajudar com seus negócios hoje?', agent: '' }]);
        setActiveSessionId(null);
    }
  };

  return (
    <div className="app-wrapper">
      <WebGLBackground />
      <div className="layout">
        <Sidebar onClearChat={handleClearChat} />
        <main className="main-content">
          <ChatArea messages={messages} typing={isTyping} />
          <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
        </main>
      </div>
    </div>
  );
}

export default App;
