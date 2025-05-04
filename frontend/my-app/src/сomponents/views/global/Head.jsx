import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { css } from '../../../styles/styles.css';
import BeelineLogo from '../../../styles/Beeline_logo.png';

const buttonCSS = {
    display: 'block',
    padding: '10px 14px 12px',
    borderRadius: '6px',
    backgroundColor: '#ffd000',
    cursor: 'pointer',
    marginLeft: '10px',
    fontSize: '18px',
};

const logoContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
};

export const Head = ({ isGitSubmitted, setIsGitSubmitted, showModal, setShowModal }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const [showNewProjectModal, setShowNewProjectModal] = React.useState(false);

    const getCurrentPage = () => {
        const path = location.pathname;
        if (path === '/main' || path === '/') return 'Главная';
        if (path.startsWith('/stat/')) return 'Архитектура';
        return '';
    };

    const confirmNewProject = () => {
        setShowNewProjectModal(false);
        setIsGitSubmitted(false);
        setShowModal(false);
        navigate('/main');
    };

    return (
        <>
            <css.HeaderContainer>
                <div style={logoContainerStyle}>
                    <css.HeaderCSS.Logo>CODEMANAGER</css.HeaderCSS.Logo>
                    <img 
                        src={BeelineLogo} 
                        alt="Beeline Logo" 
                        style={{ 
                            height: '55px',
                            width: 'auto',
                            marginLeft: '0px'
                        }} 
                    />
                </div>
                <css.HeaderCSS.MenuContainer>
                    {isGitSubmitted && (
                        <css.ModalButton 
                            onClick={() => setShowNewProjectModal(true)} 
                            style={{buttonCSS, backgroundColor:'#ffd000', fontSize: '16px', width: '90px', marginRight: '15px'}}
                        >
                            + Git
                        </css.ModalButton> 
                    )}
                    {isGitSubmitted && (
                        <css.ModalButton 
                            onClick={() => navigate('/main')} 
                            style={{
                                ...buttonCSS,
                                marginRight: '15px',
                                backgroundColor: getCurrentPage() === 'Главная' ? '#202634' : '#ffd000',
                                color: getCurrentPage() === 'Главная' ? '#ffd000' : '#202634'
                            }}
                        >
                            Главная
                        </css.ModalButton> 
                    )}
                    {isGitSubmitted && (
                        <css.ModalButton 
                            onClick={() => navigate('/stat/расход')} 
                            style={{
                                ...buttonCSS,
                                marginRight: '15px',
                                backgroundColor: getCurrentPage() === 'Архитектура' ? '#202634' : '#ffd000',
                                color: getCurrentPage() === 'Архитектура' ? '#ffd000' : '#202634'
                            }}
                        >
                            Архитектура
                        </css.ModalButton> 
                    )}
                </css.HeaderCSS.MenuContainer>
            </css.HeaderContainer>

            {showNewProjectModal && (
                <css.ModalOverlay>
                    <css.ModalContent>
                        <css.ModalTitle>Подтверждение создания проекта</css.ModalTitle>
                        <css.ModalText>
                            Вы уверены, что хотите создать новый проект? Текущий прогресс будет потерян.
                        </css.ModalText>
                        <css.ModalButton onClick={confirmNewProject}>
                            Да, создать новый проект
                        </css.ModalButton>
                        <css.ModalButtonDanger onClick={() => setShowNewProjectModal(false)}>
                            Отмена
                        </css.ModalButtonDanger>
                    </css.ModalContent>
                </css.ModalOverlay>
            )}
        </>
    );
};