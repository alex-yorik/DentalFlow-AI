from datetime import datetime

from pydantic import BaseModel


class FollowUpTask(BaseModel):
    id: str
    lead_id: str
    chat_id: int
    retry_count: int = 0
    max_retries: int = 2
    next_run_at: datetime
    status: str = "pending"
    created_at: datetime
    updated_at: datetime