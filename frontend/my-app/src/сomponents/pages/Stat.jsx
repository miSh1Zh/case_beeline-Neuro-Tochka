import React, { useState, useEffect } from "react";
import { Foot } from "../views/global/Foot";
import { useParams } from "react-router-dom";
import { DocumentationTree } from "../views/local/DocumentationTree";
import { DocumentationViewer } from "../views/local/DocumentationViewer";
import styled from "styled-components";

const DocumentationContainer = styled.div`
  display: flex;
  height: calc(100vh - 120px);
`;

const TreeContainer = styled.div`
  width: 300px;
  border-right: 1px solid #e1e1e1;
  overflow-y: auto;
  padding: 20px;
`;

const ContentContainer = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
`;

export const Stat = (props) => {
  const [documentationTree, setDocumentationTree] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState("");
  const { viewType } = useParams();

  // Загрузка дерева документации при монтировании компонента
  useEffect(() => {
    const fetchDocumentationTree = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/documentation/tree');
        const data = await response.json();
        setDocumentationTree(data.tree);
      } catch (error) {
        console.error('Error fetching documentation tree:', error);
      }
    };

    fetchDocumentationTree();
  }, []);

  // Загрузка содержимого файла при его выборе
  useEffect(() => {
    if (selectedFile) {
      const fetchFileContent = async () => {
        try {
          const response = await fetch(`http://localhost:5000/api/documentation/file?path=${encodeURIComponent(selectedFile)}`);
          const data = await response.json();
          setFileContent(data.content);
        } catch (error) {
          console.error('Error fetching file content:', error);
        }
      };

      fetchFileContent();
    }
  }, [selectedFile]);

  return (
    <>
      <DocumentationContainer>
        <TreeContainer>
          <DocumentationTree 
            tree={documentationTree} 
            onFileSelect={setSelectedFile} 
          />
        </TreeContainer>
        <ContentContainer>
          <DocumentationViewer content={fileContent} />
        </ContentContainer>
      </DocumentationContainer>
      <Foot></Foot>
    </>
  );
};