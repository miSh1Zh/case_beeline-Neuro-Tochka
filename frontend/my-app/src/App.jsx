import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import { Main } from "./сomponents/pages/Main";
import { Stat } from "./сomponents/pages/Stat";
import { Head } from "./сomponents/views/global/Head";
import { Plan } from "./сomponents/pages/Plan";

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
    </>
  );
}