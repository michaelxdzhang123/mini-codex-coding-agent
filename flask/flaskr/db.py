import sqlite3

import click

from flask import current_app, g


def get_db():
    """Connect to the application's configured database."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Close the database connection."""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    """Clear existing data and create new tables."""
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def migrate_db():
    """Add missing tables for later milestones without dropping data."""
    db = get_db()
    # M4: plan table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            author_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            assumptions TEXT,
            steps TEXT,
            files_to_inspect TEXT,
            knowledge_to_consult TEXT,
            commands_to_run TEXT,
            risks TEXT,
            raw_response TEXT,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversation (id),
            FOREIGN KEY (author_id) REFERENCES user (id)
        )
        """
    )
    # M5: patch table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS patch (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER,
            conversation_id INTEGER,
            author_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            diff_text TEXT,
            edits_json TEXT,
            status TEXT NOT NULL DEFAULT 'proposed',
            audit_log TEXT,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            applied_at TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES plan (id),
            FOREIGN KEY (conversation_id) REFERENCES conversation (id),
            FOREIGN KEY (author_id) REFERENCES user (id)
        )
        """
    )
    # M6: command_log table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS command_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER NOT NULL,
            command TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            stdout TEXT,
            stderr TEXT,
            exit_code INTEGER,
            duration_ms INTEGER,
            approved_by TEXT,
            working_directory TEXT,
            details TEXT,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES user (id)
        )
        """
    )
    # M7: repo table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS repo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES user (id)
        )
        """
    )
    db.commit()
