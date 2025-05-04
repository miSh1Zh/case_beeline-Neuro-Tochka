import React from "react";
import { Foot } from "../views/global/Foot";
import { Architecture } from "../views/local/Architecture";
import styled from "styled-components";

const Container = styled.div`
  min-height: calc(100vh - 140px);
  padding: 20px;
  background: #f5f7fa;
`;

export const Stat = () => {
  return (
    <>
      <Container>
        <Architecture />
      </Container>
      <Foot />
    </>
  );
};