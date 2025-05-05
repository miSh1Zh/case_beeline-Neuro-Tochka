import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
import { css } from '../../../styles/styles.css';

export const DocumentationViewer = ({ path }) => {
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!path) return;
    
    setIsLoading(true);
    setError('');
    setContent('');
    
    // Ensure we're sending the path without a leading slash
    const cleanPath = path.startsWith('/') ? path.slice(1) : path;
    
    fetch(`http://localhost:5001/api/documentation/${encodeURIComponent(cleanPath)}`)
      .then(res => {
        if (!res.ok) {
          console.error(`Failed to fetch: ${res.status} ${res.statusText}`);
          throw new Error(`Ошибка загрузки файла (${res.status})`);
        }
        return res.text();
      })
      .then(text => setContent(text))
      .catch(err => {
        console.error('Error fetching documentation:', err);
        setError(`Ошибка при загрузке содержимого файла: ${err.message}`);
      })
      .finally(() => setIsLoading(false));
  }, [path]);

  return (
    <css.ContentContainer>
      {isLoading && <div>Загрузка...</div>}
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {!isLoading && !error && content && (
        <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
          {content}
        </ReactMarkdown>
      )}
      {!isLoading && !error && !content && (
        <div style={{ color: '#888' }}>Выберите файл для просмотра</div>
      )}
    </css.ContentContainer>
  );
};