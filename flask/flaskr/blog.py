import json
import uuid
from pathlib import Path

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for
from flaskr.auth import login_required
from flaskr.db import get_db

# ─── M2: Model Router integration ─────────────────────────────────────
try:
    from core.models import ModelRegistry, ModelRole, ModelRouter, RoutingPolicy

    _project_root = Path(__file__).resolve().parent.parent.parent
    _model_registry = ModelRegistry(
        _project_root / "configs" / "models" / "default.yaml",
        project_root=_project_root,
    )
    _router = ModelRouter(_model_registry.load(), policy=RoutingPolicy(allow_fallback=True))
except Exception as _router_err:  # pragma: no cover
    _router = None  # type: ignore[assignment]
    import logging
    logging.getLogger(__name__).warning("Model router not available: %s", _router_err)

# ─── M3: Local RAG integration ────────────────────────────────────────
try:
    from core.rag import KnowledgeRetriever, SourceRegistry

    _rag_registry = SourceRegistry(
        _project_root / "configs" / "rag_sources" / "default.yaml",
        project_root=_project_root,
    )
    _rag_retriever = KnowledgeRetriever(_rag_registry.load())
except Exception as _rag_err:  # pragma: no cover
    _rag_retriever = None  # type: ignore[assignment]
    import logging
    logging.getLogger(__name__).warning("RAG retriever not available: %s", _rag_err)

# ─── M4: Planner integration ──────────────────────────────────────────
try:
    from core.planner import ContextBuilder, Planner

    _context_builder = ContextBuilder(retriever=_rag_retriever)
    _planner = Planner(_router, _context_builder) if _router is not None else None
except Exception as _plan_err:  # pragma: no cover
    _planner = None  # type: ignore[assignment]
    import logging
    logging.getLogger(__name__).warning("Planner not available: %s", _plan_err)

# ─── M5: Patcher integration ──────────────────────────────────────────
try:
    from core.patcher import DiffRenderer, PatchApplier, PatchProposal, PathGuard

    _patch_guard = PathGuard(allowed_roots=[_project_root / "flask"])
    _patch_applier = PatchApplier(_patch_guard)
except Exception as _patch_err:  # pragma: no cover
    _patch_applier = None  # type: ignore[assignment]
    import logging
    logging.getLogger(__name__).warning("Patcher not available: %s", _patch_err)

# ─── M6: Safe Command Runner integration ──────────────────────────────
try:
    from core.commands import CommandGuard, SafeCommandRunner, ToolWhitelistLoader

    _whitelist_loader = ToolWhitelistLoader(
        _project_root / "configs" / "tool_whitelist.yaml",
        project_root=_project_root,
    )
    _whitelist_config = _whitelist_loader.load()
    _command_guard = CommandGuard(_whitelist_config)
    _command_runner = SafeCommandRunner(_command_guard)
except Exception as _cmd_err:  # pragma: no cover
    _command_runner = None  # type: ignore[assignment]
    import logging
    logging.getLogger(__name__).warning("Command runner not available: %s", _cmd_err)


def _choose_role_for_message(message: str) -> ModelRole:
    """Simple heuristic: route coding keywords to coder, everything else to instruct."""
    coding_keywords = {
        "code", "function", "class", "def", "bug", "fix", "refactor",
        "test", "implement", "write", "error", "exception", "import",
        "module", "package", "library", "api", "endpoint", "route",
    }
    lowered = message.lower()
    if any(kw in lowered for kw in coding_keywords):
        return ModelRole.CODER
    return ModelRole.INSTRUCT

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
        _session = {
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
        # M3: vector-based retrieval from approved local knowledge
        if _rag_retriever is not None:
            try:
                rag_results = _rag_retriever.query(user_msg, top_k=3)
                for chunk in rag_results:
                    sources.append({
                        'filename': chunk.source_name,
                        'score': chunk.score,
                        'preview': chunk.text[:200] + '...',
                        'source_path': chunk.source_path,
                    })
                    rag_context += (
                        f"\n[From {chunk.source_name} — {chunk.source_path}]: "
                        f"{chunk.text[:500]}\n"
                    )
            except Exception:
                # If Chroma index is empty or misconfigured, continue silently
                pass

        # M1: keyword-based retrieval from user-uploaded documents
        docs = db.execute(
            'SELECT * FROM document WHERE author_id = ?',
            (g.user['id'],)
        ).fetchall()

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

    # ─── Generate response via M2 Model Router ──────────────────────
    prompt_context = f"\n\nRelevant documentation context:\n{rag_context}\n" if rag_context else ''

    if _router is not None:
        role = _choose_role_for_message(user_msg)
        adapter = _router.route_by_role(role)
        prompt = f"User: {user_msg}\n{prompt_context}"
        assistant_response = adapter.generate(prompt)
    else:
        # Fallback when router is unavailable
        assistant_response = (
            f"**CodeAssist AI Response**\n\n"
            f"You asked about: *{user_msg}*\n\n"
            f"Model router is unavailable.\n\n"
            f"{prompt_context}"
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


# ─── Plan Routes (M4) ─────────────────────────────────────────────────


@bp.route('/api/plan', methods=['POST'])
@login_required
def api_create_plan():
    """API: Generate a structured plan from a conversation."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    conv_id = data.get('conversation_id')
    task_description = data.get('task', '')

    if not task_description and not conv_id:
        return jsonify({'error': 'conversation_id or task required'}), 400

    db = get_db()

    # If conversation_id provided, build task from conversation title/messages
    if conv_id and not task_description:
        conv = db.execute(
            'SELECT * FROM conversation WHERE id = ? AND author_id = ?',
            (conv_id, g.user['id'])
        ).fetchone()
        if not conv:
            return jsonify({'error': 'Conversation not found'}), 404
        task_description = conv['title']

    if _planner is None:
        return jsonify({'error': 'Planner not available'}), 503

    plan = _planner.generate_plan(task_description)

    # Store plan in DB
    cursor = db.execute(
        'INSERT INTO plan (conversation_id, author_id, title, summary,'
        ' assumptions, steps, files_to_inspect, knowledge_to_consult,'
        ' commands_to_run, risks, raw_response)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            conv_id,
            g.user['id'],
            task_description[:100],
            plan.summary,
            json.dumps(plan.assumptions),
            json.dumps(plan.steps),
            json.dumps(plan.files_to_inspect),
            json.dumps(plan.knowledge_to_consult),
            json.dumps(plan.commands_to_run),
            json.dumps(plan.risks),
            plan.to_json(),
        )
    )
    db.commit()
    plan_id = cursor.lastrowid

    return jsonify({
        'plan_id': plan_id,
        'plan': {
            'summary': plan.summary,
            'assumptions': plan.assumptions,
            'steps': plan.steps,
            'files_to_inspect': plan.files_to_inspect,
            'knowledge_to_consult': plan.knowledge_to_consult,
            'commands_to_run': plan.commands_to_run,
            'risks': plan.risks,
        }
    })


@bp.route('/plans')
@login_required
def plans():
    """M4: List all generated plans."""
    db = get_db()
    rows = db.execute(
        'SELECT id, title, summary, created FROM plan'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()
    return render_template('blog/plans.html', plans=rows)


@bp.route('/plan/<int:plan_id>')
@login_required
def plan_detail(plan_id):
    """M4: Display a single structured plan."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM plan WHERE id = ? AND author_id = ?',
        (plan_id, g.user['id'])
    ).fetchone()

    if row is None:
        abort(404)

    plan = {
        'id': row['id'],
        'title': row['title'],
        'summary': row['summary'],
        'assumptions': json.loads(row['assumptions'] or '[]'),
        'steps': json.loads(row['steps'] or '[]'),
        'files_to_inspect': json.loads(row['files_to_inspect'] or '[]'),
        'knowledge_to_consult': json.loads(row['knowledge_to_consult'] or '[]'),
        'commands_to_run': json.loads(row['commands_to_run'] or '[]'),
        'risks': json.loads(row['risks'] or '[]'),
        'created': row['created'],
    }

    return render_template('blog/plan.html', plan=plan)


@bp.route('/api/plans')
@login_required
def api_plans():
    """API: List plans."""
    db = get_db()
    rows = db.execute(
        'SELECT id, title, summary, created FROM plan'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()

    return jsonify({
        'plans': [
            {
                'id': r['id'],
                'title': r['title'],
                'summary': r['summary'],
                'created': r['created'],
            }
            for r in rows
        ]
    })


# ─── Patch Routes (M5) ────────────────────────────────────────────────


@bp.route('/api/patch/propose', methods=['POST'])
@login_required
def api_propose_patch():
    """API: Propose a patch from a plan or conversation."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    plan_id = data.get('plan_id')
    conversation_id = data.get('conversation_id')
    task = data.get('task', '')

    db = get_db()

    # Derive task from plan if provided
    if plan_id and not task:
        plan_row = db.execute(
            'SELECT * FROM plan WHERE id = ? AND author_id = ?',
            (plan_id, g.user['id'])
        ).fetchone()
        if not plan_row:
            return jsonify({'error': 'Plan not found'}), 404
        task = plan_row['title']

    # Derive task from conversation if provided
    if conversation_id and not task:
        conv = db.execute(
            'SELECT * FROM conversation WHERE id = ? AND author_id = ?',
            (conversation_id, g.user['id'])
        ).fetchone()
        if not conv:
            return jsonify({'error': 'Conversation not found'}), 404
        task = conv['title']

    if not task:
        return jsonify({'error': 'task or plan_id required'}), 400

    # Build a mock patch proposal (M5 uses mock coder for generation)
    if _router is not None:
        from core.models.roles import ModelRole
        adapter = _router.route_by_role(ModelRole.CODER)
        prompt = f"Task: {task}\nGenerate a minimal code patch."
        raw = adapter.generate(prompt)
        summary = raw.splitlines()[0][:200] if raw else "Mock patch"
    else:
        summary = f"Mock patch for: {task[:80]}"

    # Create a simple placeholder edit for demonstration
    from core.patcher.patch import FileEdit
    proposal = PatchProposal(
        summary=summary,
        edits=[
            FileEdit(
                path="example.py",
                old_content="# TODO: implement\n",
                new_content=f"# TODO: implement {task[:40]}\n",
            )
        ],
    )

    diff_text = DiffRenderer.render_patch(proposal)

    cursor = db.execute(
        'INSERT INTO patch (plan_id, conversation_id, author_id, title,'
        ' summary, diff_text, edits_json, status)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (
            plan_id,
            conversation_id,
            g.user['id'],
            task[:100],
            proposal.summary,
            diff_text,
            proposal.to_json(),
            'proposed',
        )
    )
    db.commit()
    patch_id = cursor.lastrowid

    return jsonify({
        'patch_id': patch_id,
        'summary': proposal.summary,
        'diff': diff_text,
        'status': 'proposed',
    })


@bp.route('/patches')
@login_required
def patches():
    """M5: List all patch proposals."""
    db = get_db()
    rows = db.execute(
        'SELECT id, title, summary, status, created FROM patch'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()
    return render_template('blog/patches.html', patches=rows)


@bp.route('/patch/<int:patch_id>')
@login_required
def patch_detail(patch_id):
    """M5: Display a patch proposal with diff and approve/reject buttons."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM patch WHERE id = ? AND author_id = ?',
        (patch_id, g.user['id'])
    ).fetchone()

    if row is None:
        abort(404)

    patch = {
        'id': row['id'],
        'title': row['title'],
        'summary': row['summary'],
        'diff_text': row['diff_text'] or '',
        'status': row['status'],
        'created': row['created'],
        'applied_at': row['applied_at'],
    }

    return render_template('blog/patch.html', patch=patch)


@bp.route('/api/patch/<int:patch_id>/approve', methods=['POST'])
@login_required
def api_approve_patch(patch_id):
    """API: Approve and apply a patch proposal."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM patch WHERE id = ? AND author_id = ?',
        (patch_id, g.user['id'])
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Patch not found'}), 404

    if row['status'] != 'proposed':
        return jsonify({'error': f"Patch already {row['status']}"}), 400

    if _patch_applier is None:
        return jsonify({'error': 'Patch applier not available'}), 503

    try:
        proposal = PatchProposal.from_json(row['edits_json'] or '{}')
    except Exception:
        return jsonify({'error': 'Invalid patch data'}), 500

    log = _patch_applier.apply(proposal)

    db.execute(
        "UPDATE patch SET status = 'applied', applied_at = CURRENT_TIMESTAMP,"
        " audit_log = ? WHERE id = ?",
        (json.dumps(log.to_dict()), patch_id)
    )
    db.commit()

    return jsonify({
        'success': True,
        'status': 'applied',
        'files_changed': log.files,
        'errors': log.details.get('errors', []),
    })


@bp.route('/api/patch/<int:patch_id>/reject', methods=['POST'])
@login_required
def api_reject_patch(patch_id):
    """API: Reject a patch proposal without applying changes."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM patch WHERE id = ? AND author_id = ?',
        (patch_id, g.user['id'])
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Patch not found'}), 404

    if row['status'] != 'proposed':
        return jsonify({'error': f"Patch already {row['status']}"}), 400

    if _patch_applier is not None:
        try:
            proposal = PatchProposal.from_json(row['edits_json'] or '{}')
            log = _patch_applier.reject(proposal)
            audit = json.dumps(log.to_dict())
        except Exception:
            audit = None
    else:
        audit = None

    db.execute(
        "UPDATE patch SET status = 'rejected', audit_log = ? WHERE id = ?",
        (audit, patch_id)
    )
    db.commit()

    return jsonify({'success': True, 'status': 'rejected'})


@bp.route('/api/patches')
@login_required
def api_patches():
    """API: List patch proposals."""
    db = get_db()
    rows = db.execute(
        'SELECT id, title, summary, status, created FROM patch'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()

    return jsonify({
        'patches': [
            {
                'id': r['id'],
                'title': r['title'],
                'summary': r['summary'],
                'status': r['status'],
                'created': r['created'],
            }
            for r in rows
        ]
    })


# ─── Command Routes (M6) ──────────────────────────────────────────────


@bp.route('/api/command/run', methods=['POST'])
@login_required
def api_run_command():
    """API: Run a command or create a pending execution request."""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'command is required'}), 400

    command = data['command'].strip()
    if not command:
        return jsonify({'error': 'command cannot be empty'}), 400

    if _command_runner is None:
        return jsonify({'error': 'Command runner not available'}), 503

    db = get_db()

    # Validate command
    try:
        _command_runner.validate(command)
    except ValueError as e:
        # Denied immediately
        cursor = db.execute(
            'INSERT INTO command_log (author_id, command, status, stderr, details)'
            ' VALUES (?, ?, ?, ?, ?)',
            (g.user['id'], command, 'denied', str(e), json.dumps({'reason': str(e)}))
        )
        db.commit()
        return jsonify({
            'log_id': cursor.lastrowid,
            'status': 'denied',
            'error': str(e),
        }), 403

    # Check if approval is required
    needs_approval = _command_guard.requires_approval(command)
    working_dir = str(_project_root)

    if needs_approval:
        cursor = db.execute(
            'INSERT INTO command_log (author_id, command, status, working_directory)'
            ' VALUES (?, ?, ?, ?)',
            (g.user['id'], command, 'pending', working_dir)
        )
        db.commit()
        return jsonify({
            'log_id': cursor.lastrowid,
            'status': 'pending',
            'message': 'Command requires approval before execution',
            'requires_approval': True,
        })

    # Execute immediately
    result = _command_runner.run(command, working_dir=working_dir, approved_by=g.user['username'])

    cursor = db.execute(
        'INSERT INTO command_log (author_id, command, status, stdout, stderr,'
        ' exit_code, duration_ms, approved_by, working_directory, details)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            g.user['id'],
            command,
            result.status,
            result.stdout,
            result.stderr,
            result.exit_code,
            result.duration_ms,
            g.user['username'],
            working_dir,
            json.dumps({'log_id': result.log_id}),
        )
    )
    db.commit()

    return jsonify({
        'log_id': cursor.lastrowid,
        'status': result.status,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'exit_code': result.exit_code,
        'duration_ms': result.duration_ms,
    })


@bp.route('/api/command/<int:log_id>/approve', methods=['POST'])
@login_required
def api_approve_command(log_id):
    """API: Approve and run a pending command."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM command_log WHERE id = ? AND author_id = ?',
        (log_id, g.user['id'])
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Command log not found'}), 404

    if row['status'] != 'pending':
        return jsonify({'error': f"Command already {row['status']}"}), 400

    if _command_runner is None:
        return jsonify({'error': 'Command runner not available'}), 503

    command = row['command']
    working_dir = row['working_directory'] or str(_project_root)

    db.execute(
        'UPDATE command_log SET status = ?, started_at = CURRENT_TIMESTAMP'
        ' WHERE id = ?',
        ('running', log_id)
    )
    db.commit()

    result = _command_runner.run(
        command, working_dir=working_dir, approved_by=g.user['username']
    )

    db.execute(
        'UPDATE command_log SET status = ?, stdout = ?, stderr = ?,'
        ' exit_code = ?, duration_ms = ?, approved_by = ?,'
        ' completed_at = CURRENT_TIMESTAMP'
        ' WHERE id = ?',
        (
            result.status,
            result.stdout,
            result.stderr,
            result.exit_code,
            result.duration_ms,
            g.user['username'],
            log_id,
        )
    )
    db.commit()

    return jsonify({
        'success': True,
        'status': result.status,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'exit_code': result.exit_code,
        'duration_ms': result.duration_ms,
    })


@bp.route('/api/command/<int:log_id>/cancel', methods=['POST'])
@login_required
def api_cancel_command(log_id):
    """API: Cancel/reject a pending command without running it."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM command_log WHERE id = ? AND author_id = ?',
        (log_id, g.user['id'])
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Command log not found'}), 404

    if row['status'] != 'pending':
        return jsonify({'error': f"Command already {row['status']}"}), 400

    db.execute(
        "UPDATE command_log SET status = 'rejected', completed_at = CURRENT_TIMESTAMP"
        " WHERE id = ?",
        (log_id,)
    )
    db.commit()

    return jsonify({'success': True, 'status': 'rejected'})


@bp.route('/commands')
@login_required
def commands():
    """M6: List command execution history."""
    db = get_db()
    rows = db.execute(
        'SELECT id, command, status, exit_code, duration_ms, created FROM command_log'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()
    return render_template('blog/commands.html', commands=rows)


@bp.route('/command/<int:log_id>')
@login_required
def command_detail(log_id):
    """M6: Display a single command execution detail."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM command_log WHERE id = ? AND author_id = ?',
        (log_id, g.user['id'])
    ).fetchone()

    if row is None:
        abort(404)

    log = {
        'id': row['id'],
        'command': row['command'],
        'status': row['status'],
        'stdout': row['stdout'] or '',
        'stderr': row['stderr'] or '',
        'exit_code': row['exit_code'],
        'duration_ms': row['duration_ms'],
        'approved_by': row['approved_by'],
        'working_directory': row['working_directory'],
        'created': row['created'],
        'started_at': row['started_at'],
        'completed_at': row['completed_at'],
    }

    return render_template('blog/command.html', log=log)


@bp.route('/api/commands')
@login_required
def api_commands():
    """API: List command logs."""
    db = get_db()
    rows = db.execute(
        'SELECT id, command, status, exit_code, duration_ms, created FROM command_log'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()

    return jsonify({
        'commands': [
            {
                'id': r['id'],
                'command': r['command'],
                'status': r['status'],
                'exit_code': r['exit_code'],
                'duration_ms': r['duration_ms'],
                'created': r['created'],
            }
            for r in rows
        ]
    })


# ─── Repo Routes (M7) ─────────────────────────────────────────────────


@bp.route('/repos')
@login_required
def repos():
    """M7: List registered repositories."""
    db = get_db()
    rows = db.execute(
        'SELECT id, name, path, created FROM repo'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()
    return render_template('blog/repos.html', repos=rows)


@bp.route('/repo/<int:repo_id>')
@login_required
def repo_detail(repo_id):
    """M7: Browse a repository."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM repo WHERE id = ? AND author_id = ?',
        (repo_id, g.user['id'])
    ).fetchone()

    if row is None:
        abort(404)

    rel_path = request.args.get('path', '.')
    try:
        from core.repo.browser import RepoBrowser
        browser = RepoBrowser(row['path'])
        entries = browser.list_dir(rel_path)
    except Exception as e:
        flash(str(e))
        entries = []

    return render_template(
        'blog/repo.html',
        repo=row,
        entries=entries,
        current_path=rel_path,
    )


@bp.route('/repo/<int:repo_id>/file')
@login_required
def repo_file(repo_id):
    """M7: View a file in a repository."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM repo WHERE id = ? AND author_id = ?',
        (repo_id, g.user['id'])
    ).fetchone()

    if row is None:
        abort(404)

    rel_path = request.args.get('path', '')
    if not rel_path:
        abort(400)

    try:
        from core.repo.browser import RepoBrowser
        browser = RepoBrowser(row['path'])
        content = browser.read_file(rel_path)
    except Exception as e:
        flash(str(e))
        content = ''

    return render_template(
        'blog/repo_file.html',
        repo=row,
        file_path=rel_path,
        content=content,
    )


@bp.route('/api/repo', methods=['POST'])
@login_required
def api_create_repo():
    """API: Register a new repository."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    name = data.get('name', '').strip()
    path = data.get('path', '').strip()

    if not name or not path:
        return jsonify({'error': 'name and path are required'}), 400

    # Validate path exists
    from pathlib import Path
    p = Path(path)
    if not p.exists() or not p.is_dir():
        return jsonify({'error': 'Path does not exist or is not a directory'}), 400

    db = get_db()
    cursor = db.execute(
        'INSERT INTO repo (author_id, name, path) VALUES (?, ?, ?)',
        (g.user['id'], name, str(p.resolve()))
    )
    db.commit()

    return jsonify({'repo_id': cursor.lastrowid, 'name': name, 'path': str(p.resolve())})


@bp.route('/api/repos')
@login_required
def api_repos():
    """API: List registered repositories."""
    db = get_db()
    rows = db.execute(
        'SELECT id, name, path, created FROM repo'
        ' WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()

    return jsonify({
        'repos': [
            {'id': r['id'], 'name': r['name'], 'path': r['path'], 'created': r['created']}
            for r in rows
        ]
    })


@bp.route('/api/repo/<int:repo_id>/search')
@login_required
def api_repo_search(repo_id):
    """API: Search for a keyword in a repository."""
    db = get_db()
    row = db.execute(
        'SELECT * FROM repo WHERE id = ? AND author_id = ?',
        (repo_id, g.user['id'])
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Repo not found'}), 404

    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify({'error': 'q parameter required'}), 400

    try:
        from core.repo.browser import RepoBrowser
        browser = RepoBrowser(row['path'])
        results = browser.search_keyword(keyword)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'keyword': keyword, 'results': results})
