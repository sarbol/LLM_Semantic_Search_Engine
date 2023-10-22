from fastapi import FastAPI, UploadFile, HTTPException, status, BackgroundTasks
import json
from config import openai_key, cms_url
from helpers import *
import schemas
import psycopg2
import requests
import uvicorn
import time
from base import conn, postgres_table_schema


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "App is up and running"}

    
def llm_extract_variables(document: str, file_id: str, url: str):
    summary = summary_index(document)
    print(f"DOC SUMMARY: \n\n {summary}")
    result = llm_based_extraction_result(summary)
    print(f"RESULT: {result}")
    current_file_status(conn, doc_id = file_id, url = url, status = "done")
    requests.post(url = cms_url, json = result)
    time.sleep(60)
    text, search_summary, summary_vector = process_contract(document)
    db_payload = {
        "doc_id": file_id,
        "text": text,
        "summary": search_summary,
        "summary_vector": summary_vector,
        "metadata": result
    }
    
    try:
        id = insert_processed_contract_db(db_payload, conn)
    except Exception as error:
        print("Inserting into database failed")
        print(f"Error: {error}")
        conn.rollback()
    
def llm_extract_variables_list(upload_docs: dict):
    for key, doc in upload_docs.items():
        summary = summary_index(doc)
        result = llm_based_extraction_result(summary)



@app.post("/deeptech/api/process_file/", status_code = status.HTTP_202_ACCEPTED,
          response_model = schemas.FileStatus)
async def process_file(payload: schemas.Payload, background_tasks: BackgroundTasks):
    data = payload.dict()
    url = data["url"]
    print(f"URL: {url}")
    id = data["id"]
    print("ID\n", len(id))
    print(f"ID: {id}")
    response = wget_file(url = url)
    if response["status"] == "failed":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = response["message"]
        )
    else:
        file_name = response["file"]
        try:
            text = text_converter(file_name)
        except Exception as error:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Bad File"
            )
        text = text.strip()
        print(text[:100])
        if text:
            info = response["message"]
            # save_document(doc = doc, file_id = id)
        else:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Scanned PDF currently not supported"
            )
            
    current_file_status(conn, doc_id = id, url = url, status = info)
    background_tasks.add_task(llm_extract_variables, text, file_id = id, url = url)
    file_status = {
        "id": id,
        "url": url,
        "result": info
        }
    os.remove(file_name)
    return file_status

@app.get("/deeptech/api/file_status/{file_id}")
async def file_status(file_id):
    cursor = conn.cursor()
    cursor.execute(""" SELECT * FROM doc_status WHERE doc_id = %s """, (file_id,))
    d = cursor.fetchone()
    if d:
        d = {k:v for k, v in d.items()}
        return d
    else:
        return {}
    
@app.get("/deeptech/api/list")
async def list_contracts():
    cursor = conn.cursor()
    cursor.execute(
    """
        SELECT doc_id FROM document LIMIT 5;
    """
    )
    d = cursor.fetchall()
    ids = [d[i].get("doc_id") for i in range(len(d))]
    return ids


@app.get("/deeptech/api/single/{file_id}")
async def single(file_id):
    cursor = conn.cursor()
    cursor.execute(""" SELECT doc_id, metadata FROM document WHERE doc_id = %s """, (file_id,))
    d = cursor.fetchone()
    if d:
        d = {k:v for k, v in d.items()}
        return d
    else:
        return {}    
    
@app.post("/deeptech/api/search/", status_code = status.HTTP_202_ACCEPTED)
async def search(query: schemas.searchQuery):
    query  = query.dict()
    text = query.get("query")
    response = keyword_semantic_search(text, conn)
    ids = [response[i].get("doc_id") for i in range(len(response))]
    return ids


if __name__ == "__main__":
    postgres_table_schema(conn)
    uvicorn.run("main:app", host = "0.0.0.0", port = 5000, log_level = "info", reload = True)