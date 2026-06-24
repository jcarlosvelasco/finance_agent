from pydantic import BaseModel


class ReviewRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: str | None = None
