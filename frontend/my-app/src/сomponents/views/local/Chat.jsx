import React, { useState, useEffect, useRef } from 'react';
import { css } from "../../../styles/form.css";
import DeleteIcon from '../../../styles/free-icon-bin-484662.png';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  margin-top: 100px;
  margin-bottom: 50px;
  position: relative;
  z-index: 1;
  min-height: 400px;
`;

const ChatHeader = styled.div`
  display: flex;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  margin-bottom: 20px;
`;

const HeaderText = styled.div`
  font-size: 1.5rem;
  color: #202634;
  font-weight: 600;
`;

const ChatMessages = styled.div`
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 200px;
`;

const Message = styled.div`
  max-width: 70%;
  padding: 15px 20px;
  border-radius: 15px;
  background-color: ${props => props.isUser ? '#ffd000' : '#f0f2f5'};
  color: ${props => props.isUser ? '#202634' : '#333'};
  align-self: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  word-wrap: break-word;
  margin-bottom: 10px;
  margin-left: ${props => props.isUser ? 'auto' : '0'};
  margin-right: ${props => props.isUser ? '0' : 'auto'};

  &::before {
    content: '';
    position: absolute;
    top: 50%;
    ${props => props.isUser ? 'right: -10px' : 'left: -10px'};
    transform: translateY(-50%);
    border-width: 10px;
    border-style: solid;
    border-color: transparent;
    border-${props => props.isUser ? 'left' : 'right'}-color: ${props => props.isUser ? '#ffd000' : '#f0f2f5'};
  }

  pre {
    background: rgba(0, 0, 0, 0.05);
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
    margin: 10px 0;
  }

  code {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.9em;
  }

  p {
    margin: 0;
    line-height: 1.5;
  }

  ul, ol {
    margin: 10px 0;
    padding-left: 20px;
  }

  li {
    margin: 5px 0;
  }

  h1, h2, h3, h4, h5, h6 {
    margin: 15px 0 10px;
    font-weight: 600;
  }

  blockquote {
    border-left: 4px solid #ddd;
    margin: 10px 0;
    padding-left: 15px;
    color: #666;
  }
`;

const ChatInputContainer = styled.div`
  display: flex;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 15px;
  margin-top: 20px;
  gap: 10px;
  align-items: center;
  position: sticky;
  bottom: 0;
  z-index: 2;

  input {
    flex: 1;
    padding: 15px;
    border: 2px solid #eee;
    border-radius: 10px;
    font-size: 16px;
    transition: all 0.3s ease;

    &:focus {
      outline: none;
      border-color: #ffd000;
    }
  }

  button {
    padding: 15px 25px;
    background-color: #ffd000;
    color: #202634;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background-color: #ffd900;
      transform: translateY(-2px);
    }

    &:disabled {
      background-color: #ccc;
      cursor: not-allowed;
      transform: none;
    }
  }

  .delete-button {
    padding: 10px;
    background-color: #f8f9fa;
    border: 2px solid #eee;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background-color: #f0f2f5;
      border-color: #ddd;
    }

    img {
      height: 20px;
      width: auto;
    }
  }
`;

const TypingIndicator = styled.span`
  display: inline-block;
  animation: typing 1.4s infinite;

  @keyframes typing {
    0% { opacity: 0.2; }
    50% { opacity: 1; }
    100% { opacity: 0.2; }
  }
`;

export const Chat = () => {
  const [messages, setMessages] = useState([
    { text: "Привет! Я твой помощник в разработке", isUser: false }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    if (messagesEndRef.current && messages.length > 1) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [inputValue]);

  const handleSendMessage = async () => {
    if (inputValue.trim() && !isLoading) {
      const newMessage = { text: inputValue, isUser: true };
      setMessages(prev => [...prev, newMessage]);
      setInputValue('');
      setIsLoading(true);

      try {
        const response = await fetch('http://localhost:5001/api/chat', {
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
    setMessages([{ 
      text: "Привет! Я твой помощник в разработке", 
      isUser: false 
    }]);
    setShowDeleteModal(false);
  };

  const cancelDeleteHistory = () => {
    setShowDeleteModal(false);
  };

  return (
    <ChatContainer>
      <ChatHeader>
        <HeaderText>Чат с ассистентом</HeaderText>
      </ChatHeader>

      <ChatMessages>
        {messages.map((msg, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Message isUser={msg.isUser}>
              <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                {msg.text}
              </ReactMarkdown>
            </Message>
          </motion.div>
        ))}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Message isUser={false}>
              <TypingIndicator>...</TypingIndicator>
            </Message>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </ChatMessages>
      
      <ChatInputContainer>
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
          <img src={DeleteIcon} alt="Delete" />
        </button>
      </ChatInputContainer>

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
    </ChatContainer>
  );
};