/* ═══════════════════════════════════════════════════════════════
   CodeAssist AI - Main JavaScript
   ═══════════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  // ─── Utility Functions ────────────────────────────────────────

  function $(sel) { return document.querySelector(sel); }
  function $$(sel) { return document.querySelectorAll(sel); }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function formatMarkdown(text) {
    let html = escapeHtml(text);
    // Code blocks
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
      const language = lang || 'text';
      return '<pre><code class="language-' + language + '">' + code.trim() + '</code></pre>';
    });
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  function showToast(message, type) {
    type = type || 'success';
    let toast = document.getElementById('app-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'app-toast';
      toast.style.cssText = 'position:fixed;bottom:20px;right:20px;padding:12px 20px;border-radius:8px;font-size:13px;z-index:9999;transition:all 0.3s;opacity:0;transform:translateY(10px);';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.background = type === 'error' ? 'rgba(248,81,73,0.9)' : 'rgba(63,185,80,0.9)';
    toast.style.color = '#FFF';
    requestAnimationFrame(function() {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });
    setTimeout(function() {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
    }, 3000);
  }

  // ─── Initialize Highlight.js ──────────────────────────────────

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('pre code').forEach(function(block) {
      if (window.hljs) hljs.highlightElement(block);
    });
  });

  // ─── Expose globals for inline scripts ────────────────────────

  window.CodeAssist = {
    escapeHtml: escapeHtml,
    formatMarkdown: formatMarkdown,
    showToast: showToast
  };

})();
