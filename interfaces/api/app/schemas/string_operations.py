from pydantic import BaseModel

class StringInput(BaseModel):
    string1: str
    string2: str

class StringOutput(BaseModel):
    result: str 