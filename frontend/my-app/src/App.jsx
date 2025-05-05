import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import { Main } from "./сomponents/pages/Main";
import { Stat } from "./сomponents/pages/Stat";
import { Head } from "./сomponents/views/global/Head";
import { Plan } from "./сomponents/pages/Plan";
import { Architecture } from "./сomponents/views/local/Architecture";
import styled from "styled-components";

const MainContent = styled.div`
  margin-top: 80px;
  min-height: calc(100vh - 80px);
`;

export const App = () => {
  const [isGitSubmitted, setIsGitSubmitted] = useState(false);
  const [data, setData] = useState([]);
  const [showModal, setShowModal] = useState(false);
  
  const handleGitSubmit = () => {
    setIsGitSubmitted(true);
  };

  const handleNewProject = () => {
    setIsGitSubmitted(false);
    setShowModal(false);
  };

  return (
    <>
      <Head 
        isGitSubmitted={isGitSubmitted}
        setIsGitSubmitted={setIsGitSubmitted}
        showModal={showModal}
        setShowModal={setShowModal}
      />
      <MainContent>
        <Routes>
          <Route 
            path={'/main'}
            element={
              <Main 
                isGitSubmitted={isGitSubmitted} 
                onGitSubmit={handleGitSubmit}
                showModal={showModal}
                setShowModal={setShowModal}
              />
            }
          />
          <Route 
            path={'/stat/:viewType'} 
            element={<Stat statData={data}/>}
          />
          <Route
            path={'/documentation'}
            element={<Architecture />}
          />
          <Route 
            path={'*'}
            element={
              <Main 
                isGitSubmitted={isGitSubmitted} 
                onGitSubmit={handleGitSubmit}
                showModal={showModal}
                setShowModal={setShowModal}
              />
            }
          />
        </Routes>
      </MainContent>
    </>
  );
}