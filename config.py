import os
from dotenv import load_dotenv

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
cms_url = "https://contractmanagementsystem.azure-api.net/cmscontractservice/v1/document-repo/ai-doc-processing-web-hook"
                    
DUCKLING_URL = "http://duckling:8008/parse"

