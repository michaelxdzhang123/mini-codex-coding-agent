DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS conversation;
DROP TABLE IF EXISTS message;
DROP TABLE IF EXISTS document;
DROP TABLE IF EXISTS plan;
DROP TABLE IF EXISTS patch;
DROP TABLE IF EXISTS command_log;
DROP TABLE IF EXISTS repo;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE conversation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE message (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES conversation (id)
);

CREATE TABLE document (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  filename TEXT NOT NULL,
  content TEXT NOT NULL,
  chunks INTEGER NOT NULL DEFAULT 0,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE plan (
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
);

CREATE TABLE patch (
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
);

CREATE TABLE command_log (
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
);

CREATE TABLE repo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES user (id)
);
