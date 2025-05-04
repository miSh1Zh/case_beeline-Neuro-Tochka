import React from "react";
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
`;

const MainContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 60px);
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  box-sizing: border-box;
  position: relative;
  z-index: 1;
`;

const RobotContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;

  @keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-20px); }
    100% { transform: translateY(0px); }
  }
`;

const WelcomeText = styled.h1`
  font-size: 2.2rem;
  color: #202634;
  margin-bottom: 15px;
  text-align: center;
`;

const SubText = styled.p`
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 30px;
  text-align: center;
  max-width: 600px;
`;

const FormWrapper = styled.div`
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-5px);
  }
`;

const InputGroup = styled.div`
  margin-bottom: 30px;
  width: 100%;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 10px;
  font-size: 1.1rem;
  color: #202634;
  font-weight: 500;
`;

const SubmitButton = styled.button`
  width: 100%;
  padding: 15px;
  background-color: ${props => props.disabled ? '#ccc' : '#ffd000'};
  color: #202634;
  border: none;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  &:hover {
    background-color: ${props => props.disabled ? '#ccc' : '#ffd900'};
    transform: ${props => props.disabled ? 'none' : 'translateY(-2px)'};
    box-shadow: ${props => props.disabled ? '0 4px 6px rgba(0, 0, 0, 0.1)' : '0 6px 8px rgba(0, 0, 0, 0.15)'};
  }

  &:active {
    transform: translateY(0);
  }
`;

export const Main = ({ isGitSubmitted, onGitSubmit, showModal, setShowModal }) => {
    const navigate = useNavigate();
    const [gitUrl, setGitUrl] = React.useState('');
    const [branchName, setBranchName] = React.useState('main');
    const [isUrlValid, setIsUrlValid] = React.useState(false);
    const [isBranchValid, setIsBranchValid] = React.useState(true);

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

    const validation = async () => {
        if (isUrlValid && isBranchValid) {
            setShowModal(true);
            setGitUrl('');
            onGitSubmit();
        }
    };

    return(
        <RootContainer>
            {!isGitSubmitted && (
                <MainContainer>
                    <RobotContainer>
                        <img 
                            src={BeelineRobot}
                            alt="Beeline Robot" 
                            style={{ 
                                height: '120px',
                                width: 'auto',
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
                                <p style={{ color: 'red', marginTop: '5px', fontSize: '0.9rem' }}>
                                    Пожалуйста, введите корректный URL GitHub репозитория
                                </p>
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
                                <p style={{ color: 'red', marginTop: '5px', fontSize: '0.9rem' }}>
                                    Пожалуйста, введите название ветки
                                </p>
                            )}
                        </InputGroup>

                        <SubmitButton 
                            onClick={validation}
                            disabled={!isUrlValid || !isBranchValid}
                        >
                            Начать анализ
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

            <Foot />
        </RootContainer>
    )
}