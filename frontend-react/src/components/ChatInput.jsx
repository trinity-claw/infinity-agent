import React, { useState, useRef, useEffect } from 'react';

const ChatInput = ({ onSendMessage, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const resizeTextarea = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = (textareaRef.current.scrollHeight) + 'px';
    }
  };

  useEffect(() => {
    resizeTextarea();
  }, [text]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSendMessage(text.trim());
      setText('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="input-wrapper">
      <form id="chatForm" onSubmit={handleSubmit}>
        <textarea 
          ref={textareaRef}
          id="userInput" 
          placeholder="Digite sua mensagem aqui..." 
          rows="1"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <button type="submit" id="sendBtn" disabled={!text.trim() || disabled}>
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
          </svg>
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
