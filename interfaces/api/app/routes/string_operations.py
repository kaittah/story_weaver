from fastapi import APIRouter
from ..schemas.string_operations import StringInput, StringOutput

router = APIRouter(prefix="", tags=["string-operations"])

@router.post("/concatenate", response_model=StringOutput)
async def concatenate_strings(input: StringInput):
    result = input.string1 + " " + input.string2
    return {"result": result} 