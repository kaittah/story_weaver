from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your Next.js app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StringInput(BaseModel):
    string1: str
    string2: str

@app.post("/concatenate")
async def concatenate_strings(input: StringInput):
    result = input.string1 + " " + input.string2
    return {"result": result}