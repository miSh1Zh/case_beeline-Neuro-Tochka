import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
import { css } from '../../../styles/styles.css';

// Моковые данные для демонстрации
const mockDocumentation = {
  title: "Документация проекта",
  sections: [
    {
      title: "Введение",
      content: `# Введение

Это демонстрационная документация проекта. Здесь будет отображаться структура проекта и его описание.

## Основные компоненты

- Frontend (React)
- Backend (Node.js)
- База данных (MongoDB)

\`\`\`javascript
// Пример кода
const express = require('express');
const app = express();

app.get('/api/data', (req, res) => {
  res.json({ message: 'Hello World' });
});
\`\`\`
`
    },
    {
      title: "Архитектура",
      content: `# Архитектура проекта

## Структура

\`\`\`
project/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── styles/
│   └── package.json
├── backend/
│   ├── src/
│   │   ├── controllers/
│   │   ├── models/
│   │   └── routes/
│   └── package.json
└── README.md
\`\`\`

## Описание компонентов

### Frontend
- React приложение
- Material-UI для стилизации
- Redux для управления состоянием

### Backend
- Node.js сервер
- Express.js фреймворк
- MongoDB для хранения данных
`
    }
  ]
};

export const DocumentationViewer = () => {
  return (
    <css.DocumentationContainer>
      <css.DocumentationTitle>{mockDocumentation.title}</css.DocumentationTitle>
      {mockDocumentation.sections.map((section, index) => (
        <css.DocumentationSection key={index}>
          <css.SectionTitle>{section.title}</css.SectionTitle>
          <css.SectionContent>
            <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
              {section.content}
            </ReactMarkdown>
          </css.SectionContent>
        </css.DocumentationSection>
      ))}
    </css.DocumentationContainer>
  );
};