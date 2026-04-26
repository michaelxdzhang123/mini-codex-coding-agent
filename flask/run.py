#!/usr/bin/env python3
"""CodeAssist AI - Flask Application Runner"""

import os
import sys

# Add the project root to Python path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from flaskr import create_app

app = create_app()

if __name__ == '__main__':
    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize database if it doesn't exist
    db_path = os.path.join(app.instance_path, 'flaskr.sqlite')
    with app.app_context():
        from flaskr.db import init_db, migrate_db
        if not os.path.exists(db_path):
            print("[INFO] Initializing database...")
            init_db()
            print("[INFO] Database initialized.")
        else:
            migrate_db()
            print("[INFO] Database migrated.")

    print("=" * 60)
    print("  CodeAssist AI - Flask Server")
    print("  URL: http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
