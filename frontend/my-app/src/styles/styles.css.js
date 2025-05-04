import styled from "styled-components"
import { Head } from "../сomponents/views/global/Head"

export const css = {

    HeaderContainer: styled.header`
        display: flex;
        flex-direction: row;
        align-items:  center;
        justify-content: space-between;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height:  80px;
        background-color: #202634;
        padding: 0px 30px;
        z-index: 1000;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    `,

    FooterContainer: styled.footer`
        display: flex;
        flex-direction: row;
        align-items:  center;
        justify-content: space-between;
        position:  relative;
        width: 100%;
        height:  50px;
        background-color: #E5E5E5;
        margin-top: 70px;
    `,
    HeaderCSS: {
        Logo: styled.div`
            font-size: 34px;
            color: #ffd000;
        `,
        MenuContainer: styled.div`
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: flex-start;
            position: relative;
            gap: 15px;
        `,
        PageIndicator: styled.div`
            color: #ffd000;
            font-size: 18px;
            font-weight: 500;
            padding: 8px 15px;
            border-radius: 6px;
            background-color: rgba(255, 208, 0, 0.1);
            margin-right: 20px;
        `
    },
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
    DocumentationContainer: styled.div`
        display: flex;
        flex-direction: row;
        width: 100%;
        max-width: 1200px;
        min-width: 300px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        min-height: 600px;
        overflow: hidden;
    `,
    DocumentationTitle: styled.h1`
        font-size: 2.5rem;
        color: #333;
        margin-bottom: 2rem;
        text-align: center;
        width: 100%;
    `,
    DocumentationSection: styled.div`
        margin-bottom: 3rem;
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 8px;
    `,
    SectionTitle: styled.h2`
        font-size: 1.8rem;
        color: #444;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #ffd000;
    `,
    SectionContent: styled.div`
        font-size: 1.1rem;
        line-height: 1.6;
        color: #333;
        pre {
            background: #f6f8fa;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin: 1rem 0;
        }
        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
        }
        h3 {
            font-size: 1.4rem;
            color: #555;
            margin: 1.5rem 0 1rem;
        }
        ul {
            list-style-type: disc;
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }
        li {
            margin-bottom: 0.5rem;
        }
    `,
    TreeContainer: styled.div`
        width: 600px;
        padding: 1rem;
        margin-right: 20px;
        flex-shrink: 0;
        overflow: hidden;

        div {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 16px;
            color: #333;
            transition: color 0.2s;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 4px 0;

            &:hover {
                color: #ffd000;
            }
        }
    `,
    ContentContainer: styled.div`
        flex: 1;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: flex-start;
        overflow: hidden;

        pre {
            background: #f6f8fa;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            width: 100%;
        }

        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
        }

        h1, h2, h3, h4, h5, h6 {
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            color: #333;
            width: 100%;
        }

        p {
            margin-bottom: 1rem;
            line-height: 1.6;
            width: 100%;
        }

        ul, ol {
            margin-bottom: 1rem;
            padding-left: 1.5rem;
            width: 100%;
        }

        li {
            margin-bottom: 0.5rem;
        }
    `,
    EmptyContent: styled.div`
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #6c757d;
        font-size: 1.2rem;
        width: 100%;
        text-align: center;
    `,
    FinalButton: styled.button`
        padding: 15px 30px;
        border-radius: 12px;
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        color: #ffd000;
        border: 2px solid #ffd000;
        font-size: 18px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 208, 0, 0.2);
        text-transform: uppercase;
        letter-spacing: 1px;

        &:hover {
            background: linear-gradient(135deg, #1a1a1a 0%, #000000 100%);
            box-shadow: 0 6px 20px rgba(255, 208, 0, 0.3);
            transform: translateY(-2px);
        }

        &:active {
            transform: translateY(1px);
            box-shadow: 0 2px 10px rgba(255, 208, 0, 0.2);
        }
    `,
    ChatContainer: styled.div`
        display: flex;
        flex-direction: column;
        height: calc(100vh - 180px);
        max-width: 800px;
        margin: 100px auto 80px;
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        position: relative;
    `
}