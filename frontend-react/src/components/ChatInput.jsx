import React, { useEffect, useRef, useState } from 'react';

const ChatInput = ({ onSendMessage, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const resizeTextarea = () => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = 'auto';
    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
  };

  useEffect(() => {
    resizeTextarea();
  }, [text]);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!text.trim() || disabled) return;

    onSendMessage(text.trim());
    setText('');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  return (
    <div className="input-area">
      <div className="input-wrapper">
        <form id="chatForm" className="chat-form" onSubmit={handleSubmit}>
          <textarea
            ref={textareaRef}
            id="userInput"
            placeholder="Digite sua mensagem ou use as sugestoes acima..."
            rows="1"
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
          />
          <button type="submit" id="sendBtn" className="send-btn" disabled={!text.trim() || disabled}>
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
              <path stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M22 2L11 13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </form>
      </div>
      <div className="input-actions">
        <p className="input-hint">Enter para enviar - Shift+Enter para nova linha</p>
      </div>
    </div>
  );
};

export default ChatInput;
