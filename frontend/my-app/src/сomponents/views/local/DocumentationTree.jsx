import React, { useState } from 'react';
import { css } from '../../../styles/styles.css';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

// Моковые данные для демонстрации
const mockTree = {
  name: 'docs',
  type: 'directory',
  children: [
    {
      name: 'API.md',
      type: 'file',
      path: 'docs/API.md'
    },
    {
      name: 'database',
      type: 'directory',
      children: [
        {
          name: 'models.md',
          type: 'file',
          path: 'docs/database/models.md'
        },
        {
          name: 'queries.md',
          type: 'file',
          path: 'docs/database/queries.md'
        }
      ]
    },
    {
      name: 'setup',
      type: 'directory',
      children: [
        {
          name: 'linux.md',
          type: 'file',
          path: 'docs/setup/linux.md'
        },
        {
          name: 'docker.md',
          type: 'file',
          path: 'docs/setup/docker.md'
        }
      ]
    }
  ]
};

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
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleFileClick = async (path) => {
    setSelectedFile(path);
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/documentation/${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to fetch file content');
      const content = await response.text();
      setFileContent(content);
    } catch (error) {
      console.error('Error fetching file content:', error);
      setFileContent('Ошибка при загрузке содержимого файла');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <css.DocumentationContainer>
      <css.TreeContainer>
        <TreeNode node={mockTree} onFileClick={handleFileClick} />
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