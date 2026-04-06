import React, { useEffect, useRef, useState } from 'react';
import WebGLBackground from './components/WebGLBackground';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';
import AuthOverlay from './components/AuthOverlay';
import { apiUrl } from './lib/api';

const getStoredProfile = () => {
  const name = localStorage.getItem('infinity_auth_name') || '';
  const email = localStorage.getItem('infinity_auth_email') || '';
  const picture = localStorage.getItem('infinity_auth_picture') || '';
  if (!name && !email) return null;
  return { name, email, picture };
};

const sanitizeUserId = (value) => {
  const normalized = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._:-]/g, '_')
    .replace(/^[._:-]+|[._:-]+$/g, '');

  if (!normalized) return '';
  return normalized.slice(0, 100);
};

const ensureUserId = (profile) => {
  const existingRaw = localStorage.getItem('infinity_user_id');
  const existing = sanitizeUserId(existingRaw);
  if (existing) {
    if (existingRaw !== existing) {
      localStorage.setItem('infinity_user_id', existing);
    }
    return existing;
  }

  const fallbackFromEmail = profile?.email
    ? sanitizeUserId(`client_${profile.email}`)
    : 'client_web';
  const fallbackUserId = fallbackFromEmail || 'client_web';
  localStorage.setItem('infinity_user_id', fallbackUserId);
  return fallbackUserId;
};

function App() {
  const [isMobileViewport, setIsMobileViewport] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(max-width: 768px)').matches;
  });
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarOpenMobile, setIsSidebarOpenMobile] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('infinity_auth_token'),
  );
  const [userProfile, setUserProfile] = useState(() => getStoredProfile());
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const pollCursorRef = useRef(0);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;

    const mediaQuery = window.matchMedia('(max-width: 768px)');
    const handleViewportChange = (event) => {
      setIsMobileViewport(event.matches);
      if (!event.matches) {
        setIsSidebarOpenMobile(false);
      }
    };

    setIsMobileViewport(mediaQuery.matches);
    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handleViewportChange);
      return () => mediaQuery.removeEventListener('change', handleViewportChange);
    }

    mediaQuery.addListener(handleViewportChange);
    return () => mediaQuery.removeListener(handleViewportChange);
  }, []);

  useEffect(() => {
    localStorage.removeItem('infinity_chat_history');
  }, []);

  useEffect(() => {
    if (isAuthenticated && !userProfile) {
      setUserProfile(getStoredProfile());
    }
  }, [isAuthenticated, userProfile]);

  useEffect(() => {
    pollCursorRef.current = 0;
  }, [activeSessionId]);

  useEffect(() => {
    let pollingInterval;
    if (activeSessionId) {
      pollingInterval = setInterval(async () => {
        try {
          const since = pollCursorRef.current;
          const response = await fetch(apiUrl(`/v1/messages/${activeSessionId}?since=${since}`));
          if (response.ok) {
            const data = await response.json();
            if (data.messages && data.messages.length > 0) {
              const maxIndex = Math.max(...data.messages.map((message) => message.index ?? since));
              pollCursorRef.current = Math.max(pollCursorRef.current, maxIndex + 1);

              const operatorMessages = data.messages.filter((message) => message.sender === 'agent');
              if (operatorMessages.length > 0) {
                setMessages((prev) => [
                  ...prev,
                  ...operatorMessages.map((message) => ({
                    id: `session-${activeSessionId}-${message.index}`,
                    sender: 'bot',
                    text: message.content,
                    agent: 'human',
                    timestamp: message.timestamp,
                  })),
                ]);
              }
            }
          } else if (response.status === 404) {
            setActiveSessionId(null);
          }
        } catch (error) {
          console.error('Polling error', error);
        }
      }, 3000);
    }
    return () => clearInterval(pollingInterval);
  }, [activeSessionId]);

  const handleSendMessage = async (text) => {
    const trimmed = text?.trim();
    if (!trimmed) return;

    const userMsg = { sender: 'user', text: trimmed, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const userId = ensureUserId(userProfile);
      const payload = {
        message: trimmed,
        user_id: userId,
      };

      if (userProfile?.name) payload.user_name = userProfile.name;
      if (userProfile?.email) payload.user_email = userProfile.email;
      if (activeSessionId) payload.session_id = activeSessionId;

      const response = await fetch(apiUrl('/v1/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const errorPayload = await response.json();
          detail = errorPayload.detail || errorPayload.error || detail;
        } catch {
          // keep fallback detail
        }
        throw new Error(detail);
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: data.response,
          agent: data.agent_used,
          metadata: data.metadata,
          timestamp: data.timestamp,
        },
      ]);

      if (data.metadata?.escalated && data.metadata?.session_id) {
        setActiveSessionId(data.metadata.session_id);
      }
    } catch (error) {
      const detail = error instanceof Error && error.message ? `\n\nDetalhes: ${error.message}` : '';
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: `Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.${detail}`,
          agent: 'error',
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickSuggestion = (message) => {
    if (isTyping) return;
    if (isMobileViewport) setIsSidebarOpenMobile(false);
    handleSendMessage(message);
  };

  const handleToggleSidebar = () => {
    if (isMobileViewport) {
      setIsSidebarOpenMobile((prev) => !prev);
      return;
    }
    setIsSidebarCollapsed((prev) => !prev);
  };

  const handleClearChat = () => {
    if (confirm('Tem certeza que deseja apagar todo o historico?')) {
      setMessages([]);
      setActiveSessionId(null);
    }
  };

  const handleAuthSuccess = (profile) => {
    setUserProfile(profile);
    setIsAuthenticated(true);
    setMessages([]);
    setActiveSessionId(null);
    setIsSidebarOpenMobile(false);
    localStorage.removeItem('infinity_chat_history');
    ensureUserId(profile);
  };

  const handleLogout = () => {
    localStorage.removeItem('infinity_auth_token');
    localStorage.removeItem('infinity_auth_email');
    localStorage.removeItem('infinity_auth_name');
    localStorage.removeItem('infinity_auth_picture');
    localStorage.removeItem('infinity_chat_history');

    setIsAuthenticated(false);
    setUserProfile(null);
    setMessages([]);
    setActiveSessionId(null);
    setIsSidebarOpenMobile(false);
  };

  const appWrapperClass = [
    'app-wrapper',
    isSidebarCollapsed ? 'sidebar-collapsed' : '',
    isSidebarOpenMobile ? 'sidebar-open-mobile' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <>
      <WebGLBackground />
      <div className="bg-glow bg-glow-1"></div>
      <div className="bg-glow bg-glow-2"></div>

      {!isAuthenticated && <AuthOverlay onAuthSuccess={handleAuthSuccess} />}

      {isAuthenticated && (
        <div className={appWrapperClass}>
          <button
            type="button"
            className={`sidebar-overlay ${isSidebarOpenMobile ? 'visible' : ''}`}
            aria-label="Fechar menu lateral"
            onClick={() => setIsSidebarOpenMobile(false)}
          />
          <Sidebar
            onClearChat={handleClearChat}
            onQuickSuggestion={handleQuickSuggestion}
            userProfile={userProfile}
            onLogout={handleLogout}
          />
          <main className="chat-main">
            <ChatArea
              messages={messages}
              typing={isTyping}
              onSendMessage={handleSendMessage}
              userProfile={userProfile}
              onToggleSidebar={handleToggleSidebar}
            />
            <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
          </main>
        </div>
      )}
    </>
  );
}

export default App;
