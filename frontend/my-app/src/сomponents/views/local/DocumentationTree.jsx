import React, { useState, useEffect } from 'react';
import { css } from '../../../styles/styles.css';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

const TreeNode = ({ node, level = 0, onFileClick }) => {
  const [isExpanded, setIsExpanded] = useState(true);
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
  const [error, setError] = useState('');

  useEffect(() => {
    setIsLoading(true);
    fetch('http://localhost:8001/mermaid', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        path: '/',
        language: 'python'
      })
    })
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to fetch tree (${res.status})`);
        }
        return res.json();
      })
      .then(data => {
        if (data.status === 'error') {
          throw new Error(data.message);
        }
        console.log('Documentation tree loaded:', data);
        setTree(data.structure);
      })
      .catch(err => {
        console.error('Error fetching documentation tree:', err);
        setError(`Failed to load documentation structure: ${err.message}`);
        setTree(null);
      })
      .finally(() => setIsLoading(false));
  }, []);


  const handleFileClick = async (path) => {
    setSelectedFile(path);
    setIsLoading(true);
    setError('');

    try {
      console.log('Fetching file content for:', path);
      const response = await fetch(`http://localhost:5001/api/documentation/${encodeURIComponent(path)}`);

      if (!response.ok) {
        console.error(`Failed to fetch file: ${response.status} ${response.statusText}`);
        throw new Error(`Failed to fetch file (${response.status})`);
      }

      const content = await response.text();
      setFileContent(content);
    } catch (error) {
      console.error('Error fetching file content:', error);
      setError(`Error loading file content: ${error.message}`);
      setFileContent('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <css.DocumentationContainer>
      <css.TreeContainer>
        {isLoading && !tree && (
          <div>Загрузка структуры документации...</div>
        )}
        {error && !tree && (
          <div style={{ color: 'red' }}>{error}</div>
        )}
        {tree ? (
          <TreeNode node={tree} onFileClick={handleFileClick} />
        ) : (
          !isLoading && !error && <div>Документация недоступна</div>
        )}
      </css.TreeContainer>
      <css.ContentContainer>
        {isLoading && <div>Загрузка...</div>}
        {error && selectedFile && <div style={{ color: 'red' }}>{error}</div>}
        {!isLoading && !error && fileContent ? (
          <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
            {fileContent}
          </ReactMarkdown>
        ) : (
          !isLoading && !error && !selectedFile && <div style={{ color: '#888' }}>Выберите файл для просмотра</div>
        )}
      </css.ContentContainer>
    </css.DocumentationContainer>
  );
};