import { useMemo } from 'react';
import { marked } from 'marked';

/**
 * DocsViewer
 * 
 * Renderiza contenido Markdown como HTML seguro para visualización de documentación interna.
 * Nota: El contenido proviene de archivos locales (?raw), no de usuarios.
 */
const DocsViewer = ({ markdown = '', className = '' }) => {
  const html = useMemo(() => {
    // Configuración básica de marked
    marked.setOptions({
      breaks: true,
      gfm: true,
    });
    try {
      return marked.parse(markdown);
    } catch (e) {
      return `<pre class="text-red-600">Error al parsear Markdown: ${String(e)}</pre>`;
    }
  }, [markdown]);

  return (
    <article
      className={
        'prose max-w-none text-gray-100 prose-headings:text-gray-100 prose-h1:text-white prose-h2:text-white prose-h3:text-gray-200 prose-p:text-gray-200 prose-strong:text-gray-100 prose-a:text-indigo-300 hover:prose-a:text-indigo-200 prose-code:text-purple-200 prose-pre:bg-[#121621] prose-pre:border prose-pre:border-gray-700 prose-blockquote:border-l-4 prose-blockquote:border-indigo-500 prose-blockquote:bg-[#1a2130] prose-blockquote:text-indigo-200 prose-li:marker:text-indigo-300 prose-table:shadow-sm prose-th:bg-[#1e2633] prose-th:text-gray-100 prose-td:bg-[#151c26] prose-td:text-gray-200 ' +
        className
      }
      style={{
        background: 'linear-gradient(180deg, #0d1117 0%, #121621 60%, #0d1117 100%)',
        padding: '1.25rem',
        borderRadius: '0.75rem',
        border: '1px solid #1f2733',
        boxShadow: '0 4px 20px rgba(0,0,0,0.35)'
      }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export default DocsViewer;
