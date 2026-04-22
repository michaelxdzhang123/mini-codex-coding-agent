import json
import uuid
from datetime import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, current_app
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

ALLOWED_EXTENSIONS = {'txt', 'md', 'py', 'js', 'html', 'css', 'json', 'yaml', 'yml'}


# ─── Helpers ──────────────────────────────────────────────────────────


@bp.route('/')
def index():
    """Redirect to logo screen on first visit."""
    return redirect(url_for('blog.logo'))


@bp.route('/logo')
def logo():
    """M1: Logo screen - brand introduction."""
    return render_template('blog/logo.html')


@bp.route('/splash')
def splash():
    """M1: Splash screen - product reveal."""
    return render_template('blog/splash.html')


@bp.route('/menu')
@login_required
def menu():
    """M1: Main Menu / Dashboard."""
    db = get_db()
    conversations = db.execute(
        'SELECT c.id, c.title, c.created, COUNT(m.id) as msg_count'
        ' FROM conversation c LEFT JOIN message m ON c.id = m.conversation_id'
        ' WHERE c.author_id = ?'
        ' GROUP BY c.id'
        ' ORDER BY c.created DESC LIMIT 5',
        (g.user['id'],)
    ).fetchall()

    doc_count = db.execute(
        'SELECT COUNT(*) as cnt FROM document WHERE author_id = ?',
        (g.user['id'],)
    ).fetchone()['cnt']

    total_msgs = db.execute(
        'SELECT COUNT(*) as cnt FROM message m'
        ' JOIN conversation c ON m.conversation_id = c.id'
        ' WHERE c.author_id = ?',
        (g.user['id'],)
    ).fetchone()['cnt']

    return render_template('blog/menu.html',
                           conversations=conversations,
                           doc_count=doc_count,
                           total_msgs=total_msgs)


@bp.route('/chat', methods=('GET', 'POST'))
@login_required
def chat():
    """M1: Chat interface - main interaction screen."""
    conv_id = request.args.get('conv', None)
    db = get_db()

    messages = []
    current_conv = None

    if conv_id:
        current_conv = db.execute(
            'SELECT * FROM conversation WHERE id = ? AND author_id = ?',
            (conv_id, g.user['id'])
        ).fetchone()
        if current_conv:
            messages = db.execute(
                'SELECT * FROM message WHERE conversation_id = ? ORDER BY created',
                (conv_id,)
            ).fetchall()

    conversations = db.execute(
        'SELECT id, title, created FROM conversation'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()

    return render_template('blog/chat.html',
                           conversations=conversations,
                           messages=messages,
                           current_conv=current_conv)


@bp.route('/history')
@login_required
def history():
    """M1: Conversation history screen."""
    db = get_db()
    conversations = db.execute(
        'SELECT c.id, c.title, c.created,'
        ' COUNT(m.id) as msg_count,'
        ' MAX(m.created) as last_active'
        ' FROM conversation c'
        ' LEFT JOIN message m ON c.id = m.conversation_id'
        ' WHERE c.author_id = ?'
        ' GROUP BY c.id'
        ' ORDER BY last_active DESC',
        (g.user['id'],)
    ).fetchall()
    return render_template('blog/history.html', conversations=conversations)


@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    """M1: Settings screen."""
    if request.method == 'POST':
        theme = request.form.get('theme', 'dark')
        model = request.form.get('model', 'gpt-4')
        temperature = request.form.get('temperature', '0.7')
        max_tokens = request.form.get('max_tokens', '2048')
        use_rag = request.form.get('use_rag', 'off') == 'on'

        # Store in session for M1 (no user preferences table yet)
        session = {
            'theme': theme,
            'model': model,
            'temperature': float(temperature),
            'max_tokens': int(max_tokens),
            'use_rag': use_rag,
        }
        flash('Settings saved successfully!')

    return render_template('blog/settings.html')


# ─── API Endpoints ────────────────────────────────────────────────────


@bp.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """API: Process a chat message and return response."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400

    user_msg = data['message']
    conv_id = data.get('conversation_id')
    use_rag = data.get('use_rag', False)

    db = get_db()

    # Create conversation if new
    if not conv_id:
        title = user_msg[:50] + ('...' if len(user_msg) > 50 else '')
        cursor = db.execute(
            'INSERT INTO conversation (author_id, title) VALUES (?, ?)',
            (g.user['id'], title)
        )
        conv_id = cursor.lastrowid
        db.commit()

    # Save user message
    db.execute(
        'INSERT INTO message (conversation_id, role, content) VALUES (?, ?, ?)',
        (conv_id, 'user', user_msg)
    )

    # ─── Light RAG: retrieve context if enabled ─────────────────────
    sources = []
    rag_context = ''

    if use_rag:
        docs = db.execute(
            'SELECT * FROM document WHERE author_id = ?',
            (g.user['id'],)
        ).fetchall()

        # Simple keyword-based retrieval for M1
        keywords = set(user_msg.lower().split())
        scored_docs = []
        for doc in docs:
            doc_words = set(doc['content'].lower().split())
            score = len(keywords & doc_words) / max(len(keywords), 1)
            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = scored_docs[:3]

        for score, doc in top_docs:
            sources.append({
                'filename': doc['filename'],
                'score': round(score, 3),
                'preview': doc['content'][:200] + '...'
            })
            rag_context += f"\n[From {doc['filename']}]: {doc['content'][:500]}\n"

    # ─── Generate response (placeholder for M1) ─────────────────────
    prompt_context = f"\n\nRelevant documentation context:\n{rag_context}\n" if rag_context else ''

    # This is a mock response - replace with actual LLM call
    assistant_response = (
        f"**CodeAssist AI Response**\n\n"
        f"You asked about: *{user_msg}*\n\n"
        f"Here's a helpful response:\n\n"
        f"```python\n"
        f"# Example code based on your query\n"
        f"def example_function():\n"
        f"    \"\"\"This is a placeholder response.\"\"\"\n"
        f"    return 'Hello from CodeAssist AI!'\n"
        f"```\n\n"
        f"{prompt_context}\n\n"
        f"---\n"
        f"*To get real AI responses, integrate with an LLM API like OpenAI."
    )

    # Save assistant message
    db.execute(
        'INSERT INTO message (conversation_id, role, content) VALUES (?, ?, ?)',
        (conv_id, 'assistant', assistant_response)
    )
    db.commit()

    return jsonify({
        'response': assistant_response,
        'conversation_id': conv_id,
        'sources': sources
    })


@bp.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """API: Upload a document for RAG."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Unsupported file type: {ext}'}), 400

    content = file.read().decode('utf-8', errors='replace')
    chunks = max(1, len(content) // 500)

    db = get_db()
    doc_id = str(uuid.uuid4())
    db.execute(
        'INSERT INTO document (id, author_id, filename, content, chunks) VALUES (?, ?, ?, ?, ?)',
        (doc_id, g.user['id'], secure_filename(file.filename), content, chunks)
    )
    db.commit()

    return jsonify({
        'success': True,
        'doc_id': doc_id,
        'filename': secure_filename(file.filename),
        'chunks': chunks
    })


@bp.route('/api/search')
@login_required
def api_search():
    """API: Search documents using light RAG."""
    query = request.args.get('query', '')
    if not query:
        return jsonify({'results': []})

    db = get_db()
    docs = db.execute(
        'SELECT * FROM document WHERE author_id = ?',
        (g.user['id'],)
    ).fetchall()

    keywords = set(query.lower().split())
    scored = []
    for doc in docs:
        doc_words = set(doc['content'].lower().split())
        score = len(keywords & doc_words) / max(len(keywords), 1)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, doc in scored[:5]:
        results.append({
            'doc_id': doc['id'],
            'filename': doc['filename'],
            'score': round(score, 3),
            'preview': doc['content'][:300] + '...',
            'chunks': doc['chunks']
        })

    return jsonify({'results': results, 'query': query})


@bp.route('/api/history')
@login_required
def api_history():
    """API: Get conversation history."""
    db = get_db()
    conversations = db.execute(
        'SELECT c.id, c.title, c.created,'
        ' COUNT(m.id) as msg_count'
        ' FROM conversation c'
        ' LEFT JOIN message m ON c.id = m.conversation_id'
        ' WHERE c.author_id = ?'
        ' GROUP BY c.id'
        ' ORDER BY c.created DESC',
        (g.user['id'],)
    ).fetchall()

    return jsonify({
        'conversations': [
            {
                'id': c['id'],
                'title': c['title'],
                'created': c['created'],
                'msg_count': c['msg_count']
            }
            for c in conversations
        ]
    })


@bp.route('/api/conversations/<int:conv_id>/messages')
@login_required
def api_messages(conv_id):
    """API: Get messages for a specific conversation."""
    db = get_db()
    messages = db.execute(
        'SELECT m.* FROM message m'
        ' JOIN conversation c ON m.conversation_id = c.id'
        ' WHERE c.id = ? AND c.author_id = ?'
        ' ORDER BY m.created',
        (conv_id, g.user['id'])
    ).fetchall()

    return jsonify({
        'messages': [
            {
                'id': m['id'],
                'role': m['role'],
                'content': m['content'],
                'created': m['created']
            }
            for m in messages
        ]
    })


@bp.route('/api/conversations/<int:conv_id>', methods=['DELETE'])
@login_required
def api_delete_conversation(conv_id):
    """API: Delete a conversation."""
    db = get_db()
    db.execute('DELETE FROM message WHERE conversation_id = ?', (conv_id,))
    db.execute(
        'DELETE FROM conversation WHERE id = ? AND author_id = ?',
        (conv_id, g.user['id'])
    )
    db.commit()
    return jsonify({'success': True})
