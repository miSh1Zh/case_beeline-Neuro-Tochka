import React from "react"
import styled from "styled-components"

const FooterContainer = styled.footer`
    display: flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #202634;
    padding: 15px 30px;
    z-index: 1000;
    color: #888;
    font-size: 14px;
    height: 60px;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
`;

export const Foot = () => {
    return(
        <FooterContainer>
            © 2025 Neuro&Tochka. Все права защищены.
        </FooterContainer>
    )
}