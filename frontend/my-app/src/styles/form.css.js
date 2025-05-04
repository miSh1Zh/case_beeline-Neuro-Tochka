import styled from "styled-components";


export const css = {
    FormContainer: styled.div`
    display: flex;
    flex-direction:column;
    align-items:center;
    justify-content:flex-start;
    position: relative;
    width: 900px;
    height: auto;
    min-height: 60px;
    border-radius: 8px;
    box-shadow: 0px 0px 3px grey;
    margin: 0px auto 40px;
    padding: 20px;
    background-color: rgb(248, 247, 247);
    `,
    Input: styled.input`
    display: block;
    position:  relative;
    width: 100%;
    height: 40px;
    font-size: 15px;
    outline: none;
    border:  none;
    background-color: rgb(229, 229, 229);
    border-radius: 8px;
    padding-left: 14px;
    margin-bottom: 12px;
    :last-child{
        margin-bottom: 0px;
    }
    `,
    Button: styled.span`
        display: flex;
        position: relative;
        width:  220px;
        height: 44px;
        line-height: 42px;
        border-radius: 6px;
        text-align:  center;
        background-color: ${props => props.backgroundColor};
        margin-top: 10px;
        margin: auto;
        justify-content: center;
        cursor: pointer;
        &:hover {
            background-color:rgb(244, 209, 16);
            transform: scale(1.05);
        }

    `,
    TaskText: styled.h3`
        color: rgb(55, 55, 57);
        text-align: center;
        padding-top: 40px;
        width: 850px;
        height: 200px;
        margin: auto;
        padding-bottom: 200px;
    `,
    ModalOverlay: styled.div`
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `,
    ModalContent: styled.div`
        background-color: white;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0px 0px 3px grey;
        width: 500px;
        text-align: center;
    `,
    ModalTitle: styled.h2`
        color: #202634;
        margin-bottom: 20px;
    `,
    ModalText: styled.p`
        color: rgb(0, 0, 0);
        margin-bottom: 30px;
        line-height: 1.5;
    `,
    ModalButton: styled.button`
        background-color: #ffd000;
        color: #202634;
        border: none;
        padding: 12px 24px;
        border-radius: 6px;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s;
        display: block;
        margin: 0 auto;
        min-width: 200px;
        font-weight: 500;
        
        &:hover {
            background-color: #ffd900;
            transform: scale(1.05);
        }
    `,
    ModalButtonDanger: styled.button`
        background-color: rgba(226, 54, 54, 0.89);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 6px;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s;
        display: block;
        margin: 10px auto 0;
        min-width: 200px;
        font-weight: 500;
        
        &:hover {
            background-color: #ff0000;
            transform: scale(1.05);
        }
    `,
    ChatContainer: styled.div`
        width: 100%;
        max-width: 900px;
        margin: 0px auto;
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        margin-botton: 70px;
    `,

    ChatMessages: styled.div`
        overflow-y: auto;
        min-height: 650px;
        
        padding: 20px;
        background-color: #f9f9f9;

    `,
    Message: styled.div`
    padding: 8px 12px;
    margin: 5px 0;
    border-radius: 18px;
    font-size: 18px;
    max-width: 70%;
    word-wrap: break-word;
    
    background-color: ${props => props.isUser ? 'rgba(255, 208, 0, 0.79)' : '#e9e9e9'};
    color: ${props => props.isUser ? 'black' : 'black'};
    
    /* Добавляем эти свойства для выравнивания */
    margin-left: ${props => props.isUser ? 'auto' : '0'};
    margin-right: ${props => props.isUser ? '0' : 'auto'};
    text-align: ${props => props.isUser ? 'right' : 'left'};
`,
    ChatInputContainer: styled.div`
        display: flex;
        padding: 10px;
        background-color: #fff;
        border-top: 1px solid #ddd;

        input {
            flex-grow: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 8px;
            outline: none;
            font-size: 18px;
            
            &:focus {
                border-color: #ffd000;
                box-shadow: none;
            }
        }

        button {
            padding: 8px 16px;
            background-color: #ffd000;
            color: black;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 18px;

            &:hover {
                background-color: #ffd900;
            }
        }

        .delete-button {
            background-color:rgba(226, 54, 54, 0.89);
            margin-left: 8px;
            
            &:hover {
                background-color: #ff0000;
            }
        }
    `,
    BranchLabel: styled.div`
        font-size: 18px;
        color: #333;
        margin-bottom: 18px;
        font-weight: 500;
        margin-left: 10px;
    `
}