import React, { useState, useEffect } from 'react';
import { css } from '../../../styles/styles.css';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

const TreeNode = ({ node, level = 0, onFileClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isDirectory = node.type === 'directory';
  const paddingLeft = `${level * 20}px`;

  const handleClick = () => {
    if (isDirectory) {
      setIsExpanded(!isExpanded);
    } else {
      onFileClick(node.path);
    }
  };

  return (
    <div>
      <div 
        style={{ 
          paddingLeft,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          margin: '4px 0',
          userSelect: 'none'
        }}
        onClick={handleClick}
      >
        {isDirectory && (
          <span style={{ marginRight: '8px' }}>
            {isExpanded ? '📂' : '📁'}
          </span>
        )}
        {!isDirectory && <span style={{ marginRight: '8px' }}>📄</span>}
        <span>{node.name}</span>
      </div>
      {isDirectory && isExpanded && node.children && (
        <div>
          {node.children.map((child, index) => (
            <TreeNode 
              key={index} 
              node={child} 
              level={level + 1} 
              onFileClick={onFileClick}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const DocumentationTree = () => {
  const [tree, setTree] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetch('http://localhost:5001/api/documentation/tree')
      .then(res => res.json())
      .then(data => setTree(data))
      .catch(() => setTree(null));
  }, []);

  const handleFileClick = async (path) => {
    setSelectedFile(path);
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:5001/api/documentation/${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to fetch file content');
      const content = await response.text();
      setFileContent(content);
    } catch (error) {
      setFileContent('Ошибка при загрузке содержимого файла');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <css.DocumentationContainer>
      <css.TreeContainer>
        {tree ? (
          <TreeNode node={tree} onFileClick={handleFileClick} />
        ) : (
          <div>Загрузка дерева...</div>
        )}
      </css.TreeContainer>
      <css.ContentContainer>
        {isLoading ? (
          <div>Загрузка...</div>
        ) : selectedFile ? (
          <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
            {fileContent}
          </ReactMarkdown>
        ) : null}
      </css.ContentContainer>
    </css.DocumentationContainer>
  );
};