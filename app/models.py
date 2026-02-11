from pydantic import BaseModel, Field


class UploadRecord(BaseModel):
    filename: str
    content_type: str
    status: str = Field(default="accepted")
    scan_status: str = Field(default="clean")
    scan_engine: str = Field(default="mock")
    scan_detail: str = Field(default="No signature matched")
