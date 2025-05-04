import React, { useState, useEffect, useRef } from 'react';
import { css } from "../../../styles/form.css.js";
import DeleteIcon from '../../../styles/free-icon-bin-484662.png';
import BeelineRobot from '../../../styles/Beeline_Robot_input.png';

export const Chat = () => {
  const [messages, setMessages] = useState([
    { text: "Привет, я твой помощник в разработке! Чем могу помочь?", isUser: false }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // Автопрокрутка при изменении сообщений
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() && !isLoading) {
      const userMessage = inputValue.trim();
      setMessages(prev => [...prev, { text: userMessage, isUser: true }]);
      setInputValue('');
      setIsLoading(true);

      try {
        const response = await fetch('http://localhost:5000/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            message: userMessage,
            history: messages.map(msg => ({
              role: msg.isUser ? 'user' : 'assistant',
              content: msg.text
            }))
          }),
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const data = await response.json();
        setMessages(prev => [...prev, { text: data.response, isUser: false }]);
      } catch (error) {
        console.error('Error:', error);
        setMessages(prev => [...prev, { 
          text: "Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.", 
          isUser: false 
        }]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleDeleteHistory = () => {
    setShowDeleteModal(true);
  };

  const confirmDeleteHistory = () => {
    setMessages([{ text: "Привет, я твой помощник в разработке! Чем могу помочь?", isUser: false }]);
    setShowDeleteModal(false);
  };

  const cancelDeleteHistory = () => {
    setShowDeleteModal(false);
  };

  return (
    <>
      <img 
        src={BeelineRobot}
        alt="Beeline Robot" 
        style={{ 
          height: '115px',
          width: 'auto', 
          marginLeft: '1100px',
          paddingBottom: '0px',
          marginTop: '56px'
        }} 
      />
      <css.ChatContainer>
        <css.ChatMessages>
          {messages.map((msg, index) => (
            <div 
              key={index} 
              style={{
                display: 'flex',
                justifyContent: msg.isUser ? 'flex-end' : 'flex-start',
                width: '100%',
                padding: '5px 10px'
              }}
            >
              <css.Message isUser={msg.isUser}>
                {msg.text}
              </css.Message>
            </div>
          ))}
          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', width: '100%', padding: '5px 10px' }}>
              <css.Message isUser={false}>
                <span className="typing-indicator">...</span>
              </css.Message>
            </div>
          )}
          <div ref={messagesEndRef} />
        </css.ChatMessages>
        
        <css.ChatInputContainer>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Введите ваше сообщение..."
            disabled={isLoading}
          />
          <button 
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? 'Отправка...' : 'Отправить'}
          </button>
          <button 
            className="delete-button" 
            onClick={handleDeleteHistory}
            disabled={isLoading}
          >
            <img src={DeleteIcon} style={{height: '25px', width: 'auto', marginLeft: '0px'}} alt="Delete" />
          </button>
        </css.ChatInputContainer>
      </css.ChatContainer>

      {showDeleteModal && (
        <css.ModalOverlay>
          <css.ModalContent>
            <css.ModalTitle>Подтверждение удаления</css.ModalTitle>
            <css.ModalText>
              Вы уверены, что хотите удалить всю историю чата? Это действие нельзя отменить.
            </css.ModalText>
            <css.ModalButton onClick={confirmDeleteHistory}>
              Да, удалить историю
            </css.ModalButton>
            <css.ModalButtonDanger onClick={cancelDeleteHistory}>
              Отмена
            </css.ModalButtonDanger>
          </css.ModalContent>
        </css.ModalOverlay>
      )}
    </>
  );
};