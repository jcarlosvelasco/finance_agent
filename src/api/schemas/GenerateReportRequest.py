from pydantic import BaseModel


class GenerateReportRequest(BaseModel):
    ticker: str
