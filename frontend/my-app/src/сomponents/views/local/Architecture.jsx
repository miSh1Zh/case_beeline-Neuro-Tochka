import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import { Link } from 'react-router-dom';
import mermaid from 'mermaid';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import 'highlight.js/styles/github.css';
import { DocumentationTree } from './DocumentationTree';
import { DocumentationViewer } from './DocumentationViewer';

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

const renderTree = (node, level = 0, selectedFile, onSelect, expandedNodes, toggleNode, path = '') => {
  const isDirectory = node.type === 'directory';
  const isSelected = selectedFile === node.name;
  const isExpanded = expandedNodes[node.name] || false;
  const currentPath = path ? `${path}/${node.name}` : node.name;

  const handleClick = () => {
    if (isDirectory) {
      toggleNode(node.name);
    } else {
      onSelect(node, currentPath);
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
          {node.children.map(child => renderTree(child, level + 1, selectedFile, onSelect, expandedNodes, toggleNode, currentPath))}
        </div>
      )}
    </div>
  );
};

export const Architecture = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState({});
  const [activeTab, setActiveTab] = useState('documentation');
  const [mermaidDiagram, setMermaidDiagram] = useState('');
  const [architectureTree, setArchitectureTree] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const mermaidRef = useRef(null);

  useEffect(() => {
    const fetchTree = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('http://localhost:8001/hierarchy');
        if (!response.ok) {
          throw new Error('Failed to fetch tree data');
        }
        const data = await response.json();
        if (data.hierarchy) {
          setArchitectureTree(data.hierarchy);
        }
      } catch (error) {
        console.error('Error fetching tree data:', error);
        setError('Failed to fetch tree data: ' + error.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTree();
  }, []);

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
    const renderDiagram = async () => {
      if (mermaidDiagram && mermaidRef.current) {
        try {
          mermaidRef.current.innerHTML = '';

          const diagramId = `mermaid-${Date.now()}`;

          const { svg } = await mermaid.render(diagramId, mermaidDiagram);

          mermaidRef.current.innerHTML = svg;

          console.log('Diagram rendered successfully');
        } catch (error) {
          console.error('Error rendering diagram:', error);
          mermaidRef.current.innerHTML = `<div style="color: red;">Ошибка рендера диаграммы: ${error.message}</div>`;
        }
      }
    };

    renderDiagram();
  }, [mermaidDiagram]);

  const handleFileSelect = async (file, path) => {
    setSelectedFile(file.name);
    setIsLoading(true);
    setError('');
    setMermaidDiagram('');

    try {
      const response = await fetch('http://localhost:8001/mermaid', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path,
          filename: file.name
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch file content');
      }

      const mermaidText = await response.text();
      console.log('Received mermaid text:', mermaidText);

      if (mermaidText) {
        setMermaidDiagram(mermaidText);
      } else {
        throw new Error('No mermaid diagram data received');
      }

    } catch (error) {
      console.error('Error fetching file content:', error);
      setError('Failed to fetch file content: ' + error.message);
      setMermaidDiagram('');
    } finally {
      setIsLoading(false);
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
          <DocumentationTree />
        </ContentContainer>
      );
    } else {
      return (
        <ContentContainer>
          <TreeContainer>
            {isLoading && <div>Loading architecture tree...</div>}
            {error && <div style={{ color: 'red' }}>{error}</div>}
            {!isLoading && !error && architectureTree &&
              renderTree(architectureTree, 0, selectedFile, handleFileSelect, expandedNodes, toggleNode)
            }
          </TreeContainer>
          <DocumentationContainer>
            {isLoading ? (
              <div style={{ color: '#666', textAlign: 'center', marginTop: '100px' }}>
                Загрузка диаграммы...
              </div>
            ) : error ? (
              <div style={{ color: 'red', textAlign: 'center', marginTop: '100px' }}>
                {error}
              </div>
            ) : mermaidDiagram ? (
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
                        <div
                          ref={mermaidRef}
                          style={{
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            overflow: 'auto'
                          }}
                        ></div>
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
                Выберите файл для просмотра
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