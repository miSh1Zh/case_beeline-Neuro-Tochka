import React from "react";
import { useNavigate } from 'react-router-dom';
import { Chat } from "../views/local/Chat";
import { Foot } from "../views/global/Foot";
import { css } from "../../styles/form.css";
import { InputComponent } from "../comps/Input";
import BeelineRobot from '../../styles/Beeline_Robot_input.png';

export const Main = ({ isGitSubmitted, onGitSubmit, showModal, setShowModal }) => {
    const navigate = useNavigate();
    const [gitUrl, setGitUrl] = React.useState('');
    const [branchName, setBranchName] = React.useState('main');

    const validation = async () => {
        // if (gitUrl.length > 2 && branchName.length > 0) {
        //     try {
        //         const response = await fetch('http://localhost:5000/api/git-url', {
        //             method: 'POST',
        //             headers: {
        //                 'Content-Type': 'application/json',
        //             },
        //             body: JSON.stringify({ 
        //                 gitUrl: gitUrl,
        //                 branchName: branchName 
        //             }),
        //         });

        //         if (!response.ok) {
        //             throw new Error('Network response was not ok');
        //         }

        //         const data = await response.json();
        //         console.log('Success:', data);
                
        //         setShowModal(true);
        //         setGitUrl('');
        //         onGitSubmit();
        //     } catch (error) {
        //         console.error('Error:', error);
        //     }
        // }
        setShowModal(true);
        setGitUrl('');
        onGitSubmit();


    }

    return(
        <>
            {!isGitSubmitted && (
                <>
                    <img 
                        src={BeelineRobot}
                        alt="Beeline Robot" 
                        style={{ 
                            height: '115px',
                            width: 'auto', 
                            marginLeft: '980px',
                            paddingBottom: '0px',
                            marginTop: '56px'
                        }} 
                    />
                    <css.FormContainer style={{alignItems: 'flex-start'}}>
                        <InputComponent 
                            inputValue={gitUrl} 
                            action={setGitUrl} 
                            placeholder={"Введите URL вашего Git Hub"} 
                            maxLength={100}
                        />
                        <div style={{ marginTop: '20px', width: '100%' }}>
                            <css.BranchLabel>Введите название ветки</css.BranchLabel>
                            <InputComponent 
                                inputValue={branchName} 
                                action={setBranchName} 
                                placeholder={"Введите название ветки (по умолчанию: main)"} 
                                maxLength={50}
                            />
                        </div>
                        <css.Button 
                            backgroundColor={gitUrl.length > 2 && branchName.length > 0 ? "#ffd000" : "rgb(229,229,229)"}
                            onClick={validation}
                            disabled={gitUrl.length <= 2 || branchName.length === 0}
                        >
                            Отправить
                        </css.Button>
                    </css.FormContainer>
                </>
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
        </>
    )
}