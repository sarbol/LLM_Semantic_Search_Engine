from pydantic import BaseModel, HttpUrl
from typing import Union, Dict, Optional, List
from datetime import datetime

class Payload(BaseModel):
    url: HttpUrl
    id: str

    
class Extraction(BaseModel):
    category: str
    parties: Dict[str, str]
    agreement_date: Optional[str] = None
    expiration_date: Optional[str] = None
    renewal_date: Optional[str] = None
    value: Optional[str] = None
    
class FileStatus(BaseModel):
    id: str
    url: Optional[HttpUrl] = None
    result: Union[str, Extraction]
    
class FileStatusUpload(BaseModel):
    id: str
    result: Union[str, Extraction]
    
class ListFileStatusUpload(BaseModel):
    items: List[FileStatusUpload]
    

class searchQuery(BaseModel):
    query: str
