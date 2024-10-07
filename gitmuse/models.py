from pydantic import BaseModel

class StagedFile(BaseModel):
    status: str
    file_path: str

class IgnoredFile(BaseModel):
    file_path: str
