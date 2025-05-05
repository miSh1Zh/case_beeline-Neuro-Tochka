import React, { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import { Chat } from "../views/local/Chat";
import { Foot } from "../views/global/Foot";
import { css } from "../../styles/form.css";
import { InputComponent } from "../comps/Input";
import BeelineRobot from '../../styles/Beeline_Robot_input.png';
import styled from 'styled-components';

const RootContainer = styled.div`
  min-height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: ${props => props.isGitSubmitted ? 'auto' : 'hidden'};
  background: ${props => props.isGitSubmitted ? 'transparent' : 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'};
`;

const MainContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 20px;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
`;

const RobotContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
  animation: float 3s ease-in-out infinite;
  transform: scale(1);
  transition: transform 0.3s ease;

  &:hover {
    transform: scale(1.05);
  }

  @keyframes float {
    0% { transform: translateY(0px) scale(1); }
    50% { transform: translateY(-20px) scale(1.05); }
    100% { transform: translateY(0px) scale(1); }
  }
`;

const WelcomeText = styled.h1`
  font-size: 2.5rem;
  color: #202634;
  margin-bottom: 20px;
  text-align: center;
  font-weight: 700;
  background: linear-gradient(45deg, #202634, #3a4a6b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: fadeIn 0.5s ease;
`;

const SubText = styled.p`
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 40px;
  text-align: center;
  max-width: 600px;
  line-height: 1.6;
  animation: fadeIn 0.7s ease;
`;

const FormWrapper = styled.div`
  background: white;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
  transition: all 0.3s ease;
  animation: slideUp 0.5s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const InputGroup = styled.div`
  margin-bottom: 30px;
  width: 100%;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 12px;
  font-size: 1.1rem;
  color: #202634;
  font-weight: 500;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  font-size: 1.1rem;
  color: #202634;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    color: #3a4a6b;
  }

  input[type="checkbox"] {
    margin-right: 12px;
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: #ffd000;
  }
`;

const SubmitButton = styled.button`
  width: 100%;
  padding: 16px;
  background-color: ${props => props.disabled ? '#ccc' : '#ffd000'};
  color: #202634;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;

  &:hover {
    background-color: ${props => props.disabled ? '#ccc' : '#ffd900'};
    transform: ${props => props.disabled ? 'none' : 'translateY(-2px)'};
    box-shadow: ${props => props.disabled ? '0 4px 6px rgba(0, 0, 0, 0.1)' : '0 6px 8px rgba(0, 0, 0, 0.15)'};
  }

  &:active {
    transform: translateY(0);
  }

  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 5px;
    height: 5px;
    background: rgba(255, 255, 255, 0.5);
    opacity: 0;
    border-radius: 100%;
    transform: scale(1, 1) translate(-50%);
    transform-origin: 50% 50%;
  }

  &:focus:not(:active)::after {
    animation: ripple 1s ease-out;
  }

  @keyframes ripple {
    0% {
      transform: scale(0, 0);
      opacity: 0.5;
    }
    100% {
      transform: scale(20, 20);
      opacity: 0;
    }
  }
`;

const ErrorText = styled.p`
  color: #ff4444;
  margin-top: 8px;
  font-size: 0.9rem;
  animation: shake 0.5s ease;

  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }
`;

const Spinner = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', margin: '20px 0' }}>
    <div style={{
      border: '6px solid #f3f3f3',
      borderTop: '6px solid #ffd000',
      borderRadius: '50%',
      width: '40px',
      height: '40px',
      animation: 'spin 1s linear infinite'
    }} />
    <style>{`
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `}</style>
  </div>
);

const ErrorBanner = ({ message, onRetry }) => (
  <div style={{
    background: '#fff3e0',
    color: '#d84315',
    border: '1px solid #ffd000',
    borderRadius: '10px',
    padding: '18px 24px',
    margin: '20px 0',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    fontWeight: 500,
    fontSize: '1.1rem',
    boxShadow: '0 2px 8px rgba(255, 208, 0, 0.08)'
  }}>
    <span style={{ fontSize: '1.6rem' }}>⚠️</span>
    <span>{message}</span>
    {onRetry && (
      <button onClick={onRetry} style={{
        marginLeft: 'auto',
        background: '#ffd000',
        color: '#202634',
        border: 'none',
        borderRadius: '6px',
        padding: '8px 18px',
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'background 0.2s',
      }}>Повторить</button>
    )}
  </div>
);

export const Main = ({ isGitSubmitted, onGitSubmit, showModal, setShowModal }) => {
  const navigate = useNavigate();
  const [gitUrl, setGitUrl] = React.useState('');
  const [branchName, setBranchName] = React.useState('main');
  const [token, setToken] = React.useState('None');
  const [isPrivateRepo, setIsPrivateRepo] = React.useState(false);
  const [isUrlValid, setIsUrlValid] = React.useState(false);
  const [isBranchValid, setIsBranchValid] = React.useState(true);
  const [isCheckingChat, setIsCheckingChat] = useState(false);
  const [chatError, setChatError] = useState('');
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [progressMessage, setProgressMessage] = useState('');

  const validateUrl = (url) => {
    const gitUrlRegex = /^(https?:\/\/)?(www\.)?github\.com\/[a-zA-Z0-9-]+\/[a-zA-Z0-9-_.]+(?:\/)?$/;
    return gitUrlRegex.test(url);
  };

  const handleUrlChange = (value) => {
    setGitUrl(value);
    setIsUrlValid(validateUrl(value));
  };

  const handleBranchChange = (value) => {
    setBranchName(value);
    setIsBranchValid(value.length > 0);
  };

  const handleTokenChange = (value) => {
    setToken(value);
  };

  const handlePrivateRepoChange = (e) => {
    setIsPrivateRepo(e.target.checked);
    if (!e.target.checked) {
      setToken('None');
    }
  };

  // Функция для проверки статуса задачи
  const checkJobStatus = async (id) => {
    try {
      const response = await fetch(`http://localhost:5001/api/job/${id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }
      const data = await response.json();
      setJobStatus(data.status);

      switch (data.status) {
        case 'PENDING':
          setProgressMessage('Задача в очереди...');
          break;
        case 'STARTED':
          setProgressMessage('Анализ репозитория...');
          break;
        case 'SUCCESS':
          setProgressMessage('Анализ завершен!');
          setShowModal(true);
          setGitUrl('');
          onGitSubmit();
          setIsCheckingChat(false);
          setJobId(null);
          setJobStatus(null);
          return true;
        case 'FAILURE':
          setChatError(data.error || 'Произошла ошибка при анализе репозитория');
          setIsCheckingChat(false);
          setJobId(null);
          setJobStatus(null);
          return true;
        default:
          setProgressMessage('Обработка...');
      }
      return false;
    } catch (error) {
      console.error('Error checking job status:', error);
      setChatError('Ошибка при проверке статуса задачи');
      setIsCheckingChat(false);
      setJobId(null);
      setJobStatus(null);
      return true;
    }
  };

  // Эффект для отслеживания статуса задачи
  useEffect(() => {
    let intervalId;
    if (jobId && isCheckingChat) {
      intervalId = setInterval(async () => {
        const shouldStop = await checkJobStatus(jobId);
        if (shouldStop) {
          clearInterval(intervalId);
        }
      }, 2000); // Проверяем каждые 2 секунды
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [jobId, isCheckingChat]);

  const validation = async () => {
    if (isUrlValid && isBranchValid) {
      setIsCheckingChat(true);
      setChatError('');
      setProgressMessage('Отправка запроса...');
      try {
        const response = await fetch('http://localhost:5001/api/clone', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            repo_url: gitUrl,
            branch: branchName,
            token: isPrivateRepo ? token : 'None'
          }),
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const data = await response.json();
        if (data.job_id) {
          setJobId(data.job_id);
          setProgressMessage('Задача создана, ожидание...');
        } else {
          throw new Error('No job ID received');
        }
      } catch (error) {
        console.error('Error:', error);
        setChatError('Ошибка соединения с сервером');
        setIsCheckingChat(false);
      }
    }
  };

  return (
    <RootContainer isGitSubmitted={isGitSubmitted}>
      {!isGitSubmitted && (
        <MainContainer>
          <RobotContainer>
            <img
              src={BeelineRobot}
              alt="Beeline Robot"
              style={{
                height: '150px',
                width: 'auto',
                filter: 'drop-shadow(0 10px 20px rgba(0, 0, 0, 0.1))'
              }}
            />
          </RobotContainer>

          <WelcomeText>Добро пожаловать в CodeManager!</WelcomeText>
          <SubText>
            Введите URL вашего GitHub репозитория и выберите ветку, чтобы начать анализ кода
          </SubText>

          <FormWrapper>
            <InputGroup>
              <Label>URL GitHub репозитория</Label>
              <InputComponent
                inputValue={gitUrl}
                action={handleUrlChange}
                placeholder={"https://github.com/username/repository"}
                maxLength={100}
              />
              {gitUrl && !isUrlValid && (
                <ErrorText>
                  Пожалуйста, введите корректный URL GitHub репозитория
                </ErrorText>
              )}
            </InputGroup>

            <InputGroup>
              <Label>Название ветки</Label>
              <InputComponent
                inputValue={branchName}
                action={handleBranchChange}
                placeholder={"main"}
                maxLength={50}
              />
              {!isBranchValid && (
                <ErrorText>
                  Пожалуйста, введите название ветки
                </ErrorText>
              )}
            </InputGroup>

            <InputGroup>
              <CheckboxLabel>
                <input
                  type="checkbox"
                  checked={isPrivateRepo}
                  onChange={handlePrivateRepoChange}
                />
                Приватный репозиторий
              </CheckboxLabel>
              {isPrivateRepo && (
                <>
                  <Label>Введите токен доступа</Label>
                  <InputComponent
                    inputValue={token}
                    action={handleTokenChange}
                    placeholder={"None"}
                    maxLength={100}
                    type="password"
                  />
                </>
              )}
            </InputGroup>

            <SubmitButton
              onClick={validation}
              disabled={!isUrlValid || !isBranchValid || isCheckingChat}
            >
              {isCheckingChat ? 'Анализ...' : 'Начать анализ'}
            </SubmitButton>
          </FormWrapper>
        </MainContainer>
      )}

      {isGitSubmitted && <Chat />}

      {showModal && (
        <css.ModalOverlay>
          <css.ModalContent>
            <css.ModalTitle>Успешно!</css.ModalTitle>
            <css.ModalText>
              Архитектура проекта и документация были успешно сгенерированы и отправлены на страницу архитектуры.
            </css.ModalText>
            <css.ModalButton onClick={() => {
              setShowModal(false);
            }}>
              Перейти к чату
            </css.ModalButton>
          </css.ModalContent>
        </css.ModalOverlay>
      )}

      {isCheckingChat && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'white',
          padding: '20px',
          borderRadius: '10px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 1000,
          textAlign: 'center'
        }}>
          <Spinner />
          <p style={{ marginTop: '15px', color: '#666' }}>{progressMessage}</p>
        </div>
      )}
      {chatError && <ErrorBanner message={chatError} onRetry={validation} />}

      <Foot />
    </RootContainer>
  )
}