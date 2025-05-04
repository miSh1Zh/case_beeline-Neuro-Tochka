import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import { Link } from 'react-router-dom';
import mermaid from 'mermaid';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import 'highlight.js/styles/github.css';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  margin-top: 100px;
  margin-bottom: 80px;
  min-height: 400px;
`;

const NavigationBar = styled.div`
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: #f8f9fa;
  border-radius: 15px 15px 0 0;
  margin-bottom: 20px;
  border-bottom: 2px solid #f0f2f5;
`;

const HomeButton = styled(Link)`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #ffd000;
  color: #202634;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;

  &:hover {
    background: #ffd900;
    transform: translateY(-1px);
  }
`;

const Breadcrumbs = styled.div`
  display: flex;
  align-items: center;
  margin-left: 20px;
  color: #666;
  font-size: 0.9rem;
`;

const BreadcrumbItem = styled(Link)`
  color: #666;
  text-decoration: none;
  transition: color 0.3s ease;

  &:hover {
    color: #202634;
  }

  &:after {
    content: '/';
    margin: 0 8px;
    color: #666;
  }

  &:last-child:after {
    display: none;
  }
`;

const ContentContainer = styled.div`
  display: flex;
  flex: 1;
  padding: 20px;
`;

const TreeContainer = styled.div`
  width: 300px;
  border-right: 2px solid #f0f2f5;
  padding: 20px;
  overflow-y: auto;
  background: #f8f9fa;
  border-radius: 15px 0 0 15px;
`;

const DocumentationContainer = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: white;
  border-radius: 0 15px 15px 0;
`;

const TreeNode = styled.div`
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  color: ${props => props.isSelected ? '#202634' : '#666'};
  background: ${props => props.isSelected ? '#ffd000' : 'transparent'};

  &:hover {
    background: ${props => props.isSelected ? '#ffd900' : '#f0f2f5'};
  }
`;

const TreeIcon = styled.span`
  font-size: 1.2rem;
  color: ${props => props.isSelected ? '#202634' : '#666'};
`;

const MarkdownContent = styled.div`
  h1, h2, h3, h4, h5, h6 {
    color: #202634;
    margin: 20px 0 10px;
  }

  p {
    color: #666;
    line-height: 1.6;
    margin-bottom: 15px;
  }

  pre {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 15px 0;
  }

  code {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.9em;
  }

  ul, ol {
    margin: 15px 0;
    padding-left: 20px;
  }

  li {
    margin: 8px 0;
    color: #666;
  }

  blockquote {
    border-left: 4px solid #ffd000;
    margin: 15px 0;
    padding-left: 15px;
    color: #666;
  }
`;

const TabsContainer = styled.div`
  display: flex;
  gap: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 15px 15px 0 0;
  border-bottom: 2px solid #f0f2f5;
  margin-bottom: 20px;
`;

const TabButton = styled(motion.button)`
  padding: 15px 30px;
  font-size: 1.2rem;
  font-weight: 600;
  color: ${props => props.active ? '#202634' : '#666'};
  background: ${props => props.active ? '#ffd000' : 'transparent'};
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: ${props => props.active ? '0 4px 12px rgba(255, 208, 0, 0.3)' : 'none'};

  &:hover {
    color: #202634;
    background: ${props => props.active ? '#ffd900' : '#f0f2f5'};
    transform: translateY(-2px);
  }

  &::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 100%;
    height: 3px;
    background: #ffd000;
    transform: scaleX(${props => props.active ? 1 : 0});
    transform-origin: left;
    transition: transform 0.3s ease;
  }
`;

const ArchitectureContent = styled.div`
  padding: 20px;
  background: white;
  border-radius: 10px;
  margin-top: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
`;

const MermaidContainer = styled.div`
  width: 100%;
  height: 600px;
  background: white;
  border-radius: 10px;
  padding: 20px;
  overflow: hidden;
  position: relative;

  .mermaid {
    min-width: 800px;
    min-height: 600px;
    transform-origin: center;
  }

  svg {
    width: 100%;
    height: 100%;
  }
`;

const Controls = styled.div`
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

const ControlButton = styled.button`
  padding: 8px 12px;
  background: #f0f2f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;

  &:hover {
    background: #ffd000;
  }
`;

// Моковые данные для демонстрации
const mockTree = {
  name: 'docs',
  type: 'directory',
  children: [
    {
      name: 'chat',
      type: 'directory',
      children: [
        {
          name: 'ChatCore.__init__.md',
          type: 'file',
          content: `# Documentation for \`ChatCore.__init__\`

## Overview

The \`__init__\` method is the constructor for the \`ChatCore\` class. It initializes an instance of \`ChatCore\` with a specified dimensionality for its internal data store.

## Method Signature

\`\`\`python
def __init__(self, dim=1536):
\`\`\`

## Parameters

- **dim** (int, optional): The dimensionality of the vectors stored within the \`ChatCore\` instance. Defaults to \`1536\`.

## Description

When a new \`ChatCore\` object is instantiated, the constructor initializes an internal data store by creating an instance of \`HybridStore\` with the specified dimensionality (\`dim\`). This store is assigned to the instance variable \`self.store\`.

## Implementation Details

- **\`self.store\`**: An instance of \`HybridStore\`, configured to handle vectors of dimension \`dim\`.
- **\`HybridStore\`**: Presumably a class responsible for storing and managing high-dimensional vector data, possibly supporting hybrid storage mechanisms (e.g., combining in-memory and persistent storage).

## Usage Example

\`\`\`python
# Create a ChatCore instance with default vector dimension (1536)
chat = ChatCore()

# Create a ChatCore instance with a custom vector dimension
custom_chat = ChatCore(dim=1024)
\`\`\`

## Notes

- The default dimension (\`1536\`) suggests compatibility with models or embeddings that produce vectors of this size.
- Adjusting \`dim\` allows flexibility if different embedding sizes are used.

## Dependencies

- **\`HybridStore\`**: A class that must be defined elsewhere in the codebase. It should accept an integer parameter specifying vector dimensions during initialization.

---

**Summary:**  
The \`__init__\` method sets up the core data storage component of \`ChatCore\` with a specified vector dimension, enabling the class to handle high-dimensional vector data efficiently.`
        },
        {
          name: 'ChatCore.ingest.md',
          type: 'file',
          content: '# Documentation for `ChatCore.ingest`'
        }
      ]
    },
    {
      name: 'api',
      type: 'directory',
      children: [
        {
          name: 'endpoints.md',
          type: 'file',
          content: '# API Endpoints Documentation'
        }
      ]
    }
  ]
};

const mockArchitectureTree = {
  name: 'frontend',
  type: 'directory',
  children: [
    {
      name: 'app_frontend',
      type: 'directory',
      children: [
        {
          name: 'src',
          type: 'directory',
          children: [
            {
              name: 'App.js',
              type: 'file',
              mermaid: `
flowchart LR
  classDef file   fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,padding:10px;
  classDef folder fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,stroke-dasharray:5 5,padding:10px;

  subgraph frontend_app_frontend_src[frontend/app_frontend/src]
    Func_App["App()"]
    Target["App.js"]
    App_test_js["App.test.js"]
    Func_getUserFromStorage["getUserFromStorage()"]
    index_js["index.js"]
  end

  index_js -- Target
  index_js -- Func_App
  App_test_js -- Target
  App_test_js -- Func_App
  Func_getUserFromStorage -- Target
  Func_App -- Target

  class Target file
  class Func_App file
  class Func_getUserFromStorage file
  class index_js file
  class App_test_js file
`
            }
          ]
        }
      ]
    }
  ]
};

const renderTree = (node, level = 0, selectedFile, onSelect, expandedNodes, toggleNode) => {
  const isDirectory = node.type === 'directory';
  const isSelected = selectedFile === node.name;
  const isExpanded = expandedNodes[node.name] || false;

  const handleClick = () => {
    if (isDirectory) {
      toggleNode(node.name);
    } else {
      onSelect(node);
    }
  };

  return (
    <div key={node.name}>
      <TreeNode
        isSelected={isSelected}
        onClick={handleClick}
        style={{ paddingLeft: `${level * 20}px` }}
      >
        <TreeIcon isSelected={isSelected}>
          {isDirectory ? (isExpanded ? '📂' : '📁') : '📄'}
        </TreeIcon>
        {node.name}
      </TreeNode>
      {isDirectory && isExpanded && node.children && (
        <div>
          {node.children.map(child => renderTree(child, level + 1, selectedFile, onSelect, expandedNodes, toggleNode))}
        </div>
      )}
    </div>
  );
};

export const Architecture = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentation, setDocumentation] = useState('');
  const [expandedNodes, setExpandedNodes] = useState({});
  const [activeTab, setActiveTab] = useState('documentation');
  const [mermaidDiagram, setMermaidDiagram] = useState('');
  const mermaidRef = useRef(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      flowchart: {
        diagramPadding: 30,
        nodeSpacing: 150,
        rankSpacing: 100,
        curve: 'basis'
      }
    });
  }, []);

  useEffect(() => {
    if (mermaidDiagram && mermaidRef.current) {
      // Очищаем контейнер
      mermaidRef.current.innerHTML = '';
      // Рендерим диаграмму
      try {
        mermaid.render('mermaid-svg', mermaidDiagram, (svgCode) => {
          mermaidRef.current.innerHTML = svgCode;
        });
      } catch (e) {
        mermaidRef.current.innerHTML = '<div style="color: red;">Ошибка рендера диаграммы: ' + e.message + '</div>';
      }
    }
  }, [mermaidDiagram]);

  const handleFileSelect = (file) => {
    setSelectedFile(file.name);
    if (activeTab === 'documentation') {
      setDocumentation(file.content);
    } else {
      setMermaidDiagram(file.mermaid);
    }
  };

  const toggleNode = (nodeName) => {
    setExpandedNodes(prev => ({
      ...prev,
      [nodeName]: !prev[nodeName]
    }));
  };

  const renderContent = () => {
    if (activeTab === 'documentation') {
      return (
        <ContentContainer>
          <TreeContainer>
            {renderTree(mockTree, 0, selectedFile, handleFileSelect, expandedNodes, toggleNode)}
          </TreeContainer>
          <DocumentationContainer>
            {documentation ? (
              <MarkdownContent>
                <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                  {documentation}
                </ReactMarkdown>
              </MarkdownContent>
            ) : (
              <div style={{ color: '#666', textAlign: 'center', marginTop: '100px' }}>
                Выберите файл документации для просмотра
              </div>
            )}
          </DocumentationContainer>
        </ContentContainer>
      );
    } else {
      return (
        <ContentContainer>
          <TreeContainer>
            {renderTree(mockArchitectureTree, 0, selectedFile, handleFileSelect, expandedNodes, toggleNode)}
          </TreeContainer>
          <DocumentationContainer>
            {mermaidDiagram ? (
              <MermaidContainer>
                <TransformWrapper
                  initialScale={1}
                  minScale={0.5}
                  maxScale={3}
                  centerOnInit={true}
                >
                  {({ zoomIn, zoomOut, resetTransform }) => (
                    <>
                      <TransformComponent>
                        <div ref={mermaidRef}></div>
                      </TransformComponent>
                      <Controls>
                        <ControlButton onClick={() => zoomIn()}>
                          <span>🔍</span> Увеличить
                        </ControlButton>
                        <ControlButton onClick={() => zoomOut()}>
                          <span>🔍</span> Уменьшить
                        </ControlButton>
                        <ControlButton onClick={() => resetTransform()}>
                          <span>🔄</span> Сбросить
                        </ControlButton>
                      </Controls>
                    </>
                  )}
                </TransformWrapper>
              </MermaidContainer>
            ) : (
              <div style={{ color: '#666', textAlign: 'center', marginTop: '100px' }}>
                Выберите файл для просмотра архитектуры
              </div>
            )}
          </DocumentationContainer>
        </ContentContainer>
      );
    }
  };

  return (
    <Container>
      <TabsContainer>
        <TabButton
          active={activeTab === 'documentation'}
          onClick={() => setActiveTab('documentation')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          📚 Документация
        </TabButton>
        <TabButton
          active={activeTab === 'architecture'}
          onClick={() => setActiveTab('architecture')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          🏗️ Архитектура
        </TabButton>
      </TabsContainer>
      {renderContent()}
    </Container>
  );
}; 