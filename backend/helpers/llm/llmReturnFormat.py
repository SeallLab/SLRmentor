from pydantic import BaseModel

class Response(BaseModel):
    text: str
    updated_search_string: str
    has_changed: bool

class ResponseCriteria(BaseModel):
    text: str
    updated_inclusion_exclusion_criteria: str
    has_changed: bool

class ResponseMentor(BaseModel):
    text: str
    has_changed: bool