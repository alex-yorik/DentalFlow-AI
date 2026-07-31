SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    telegram_chat_id INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'new',
    name TEXT,
    phone TEXT,
    email TEXT,
    service_interest TEXT,
    intent TEXT,
    urgency TEXT,
    preferred_time TEXT,
    source TEXT NOT NULL DEFAULT 'telegram',
    qualification_score INTEGER NOT NULL DEFAULT 0,
    conversation_summary TEXT NOT NULL DEFAULT '',
    opt_in_consent INTEGER NOT NULL DEFAULT 0,
    internal_tags TEXT NOT NULL DEFAULT '[]',
    crm_contact_id TEXT,
    followup_task_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_telegram_chat_id ON leads(telegram_chat_id);
CREATE INDEX IF NOT EXISTS idx_leads_state ON leads(state);
"""