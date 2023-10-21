import docxpy
from PyPDF2 import PdfReader
import os
from os.path import splitext, basename
from urllib.parse import urlparse
import json
import spacy
import re
import requests
import numpy as np
import datetime
import openai
import psycopg2
import wget
from config import *
from prompt import *


nlp = spacy.load("en_core_web_sm")

openai.api_key = openai_key

    

date_filter = re.compile(r"\d{4}-\d{2}-\d{2}")


class UnsupportedFileType(Exception):
    def __init__(self, extension):
        self.extension = extension
        self.message = f"This filetype => {self.extension} is not supported\n pass[.pdf, .docx] files"
        super().__init__(self.message)

def text_converter(file_path):
    extension = os.path.splitext(file_path)[-1]
    print(f"FILE EXTENSION: {extension}")
    
    if extension.lower() == ".pdf":
        reader = PdfReader(file_path)
        pages = len(reader.pages)
        merge_text = [reader.pages[i].extract_text() for i in range(pages)]
        return "\n\n".join(merge_text)
            
    elif extension.lower() in [".docx", ".doc"]:
        text = docxpy.process(file_path)
        return text
    else:
        raise UnsupportedFileType(extension)
    
def extract_term(string):
    data = {
        "text": string
    }
    resp = requests.post(DUCKLING_URL, data)
    if resp.status_code == 200:
        result = json.loads(resp.text)
        for i in range(len(result)):
            try:
                value = result[i]["value"]["normalized"]["value"]
            except:
                continue
        try:
            return value
        except UnboundLocalError:
            return None
    else:
        return None
    
def duckling_time_entity(text: str):
    body = {
        "text": text
    }
    response = requests.post(DUCKLING_URL, body)
    if response.status_code == 200:
        result = json.loads(response.text)
        time_entity = [r for r in result if r["dim"] in ["time", "duration"]]
        if time_entity:
            entity = time_entity[0]
            entity_dim = entity["dim"]
            if entity_dim == "duration":
                value = entity["value"]["normalized"]["value"]
                result = {"dim": entity_dim, "value":value}
            else:
                value = entity["value"]["value"]
                value = value.split("T")[0]
                result = {"dim": entity_dim, "value":value}
        else:
            result = None
    else:
        result = None
    
    return result


def duckling_money_entity(text: str):
    body = {
        "text": text
    }
    response = requests.post(DUCKLING_URL, body)
    if response.status_code == 200:
        result = json.loads(response.text)
        money_entity = {r["dim"]:r["value"]["value"] for r in result if r["dim"] in ["amount-of-money", "distance", "number", "phone-number"]}
        if money_entity:
            value = money_entity.get("amount-of-money", None) or money_entity.get("number", None) or money_entity.get("distance", None)
        else:
            value = None
    else:
        value = None
    
    return value

def extract_date(string):
    data = {
        "text": string
    }
    resp = requests.post(DUCKLING_URL, data)
    if resp.status_code == 200:
        result = json.loads(resp.text)
        try:
            value = result[0]["value"]["value"]
            value = value.split("T")[0]
        except:
            value = None
    else:
        value = None
    return value



def get_completion(message: str = None):
    completion = openai.ChatCompletion.create(
        model = "gpt-4",
        messages = message
    )
    return completion.choices[0].message

def refine_response(prompt):
    message = [
        {"role": "system", "content":SYSTEM_MESSAGE},
        {"role": "user", "content": prompt}
    ]
    refined = get_completion(message = message)
    return refined

        
def download_file(url: str = None):
    session = requests.Session()
    response = session.get(url, stream = True)
    if response.status_code == 200:
        path = urlparse(url).path
        file_name = basename(path)
        ext = splitext(path)[-1]
        if ext.lower() in [".pdf", ".docx", ".doc"]:
            with open(f"./uploads/{file_name}", "wb") as f:
                f.write(response.content)
            info = "pending"
            status = "success"
        else:
            info = "Unsupported file type => .docx, .doc or .pdf only"
            status = "failed"
    else:
        info = "url error"
        status = "failed"
    
    return {
        "status": status,
        "message": info,
        "file": file_name
    }
    
def wget_file(url: str = None):
    try:
        filename = wget.download(url)
        print("downloaded")
        return {
            "status": "success",
            "message": "pending",
            "file": filename
        }
    except Exception as error:
        print(f"Error: {error}")
        return {
            "status": "failed",
            "message": error,
            "file": None
        }
    
    

def summary_index(doc: str):
    text = " ".join(doc.split()[:5000])
    prompt = extract_relevant_context_prompts(text)
    llm_response = refine_response(prompt)
    summary = llm_response["content"]
    return summary


def validate_agreement_date(extracted_date: str):
    date_pattern = "\d{2,}-\d{2,}-\d{4,}"
    matcher = re.compile(date_pattern)
    if bool(re.match(matcher, extracted_date)):
        return extracted_date
    elif extracted_date.lower() == "null":
        return None
    else:
        refine_date = duckling_time_entity(extracted_date)
        if refine_date and refine_date["dim"] == "time":
            return refine_date["value"]
        else:
            return None

def infer_date_pattern(date_str: str):
    year_first = "\d{4,}-\d{2,}-\d{2,}"
    day_first = "\d{2,}-\d{2,}-\d{4,}"
    
    year_pattern = re.compile(year_first)
    day_pattern = re.compile(day_first)
    
    if date_str and bool(re.match(year_pattern, date_str)):
        return "year_first"
    elif date_str and bool(re.match(day_pattern, date_str)):
        return "day_first"
    else:
        return None
        
def compute_expiration_date(agreement_date: str, expiration_date: dict):
    if agreement_date and expiration_date:
        if expiration_date["dim"] == "duration":
            date_pattern = infer_date_pattern(agreement_date)
            if date_pattern and date_pattern == "year_first":
                agreement_date = datetime.datetime.strptime(agreement_date, "%Y-%m-%d")
                duration = expiration_date["value"]
                expiration_date = agreement_date + datetime.timedelta(seconds = duration)
                expiration_date = datetime.datetime.strftime(expiration_date, "%Y-%m-%d")
            elif date_pattern and date_pattern == "day_first":
                agreement_date = datetime.datetime.strptime(agreement_date, "%d-%m-%Y")
                duration = expiration_date["value"]
                expiration_date = agreement_date + datetime.timedelta(seconds = duration)
                expiration_date = datetime.datetime.strftime(expiration_date, "%Y-%m-%d")
            else:
                expiration_date = None
        else:
            expiration_date = expiration_date["value"]
    else:
        expiration_date = None
        
    return expiration_date

def compute_renewal_date(agreement_date: str, renewal_date: dict):
    if agreement_date and renewal_date:
        if renewal_date["dim"] == "duration":
            date_pattern = infer_date_pattern(agreement_date)
            if date_pattern and date_pattern == "year_first":
                agreement_date = datetime.datetime.strptime(agreement_date, "%Y-%m-%d")
                duration = renewal_date["value"]
                renewal_date = agreement_date + datetime.timedelta(seconds = duration)
                renewal_date = datetime.datetime.strftime(renewal_date, "%Y-%m-%d")
            elif date_pattern and date_pattern == "day_first":
                agreement_date = datetime.datetime.strptime(agreement_date, "%d-%m-%Y")
                duration = renewal_date["value"]
                renewal_date = agreement_date + datetime.timedelta(seconds = duration)
                renewal_date = datetime.datetime.strftime(renewal_date, "%d-%m-%Y")
            else:
                renewal_date = None
        else:
            renewal_date = renewal_date["value"]
    else:
        renewal_date = None
    
    return renewal_date
            

def extract_parties(summary: str):
    prompt = parties_prompt(summary = summary)
    response = refine_response(prompt)
    try:
        parties = json.loads(response["content"])
    except:
        parties = {"Party A": "null"}
    return parties

def extract_category(summary: str):
    prompt = category_prompt(summary = summary)
    response = refine_response(prompt)
    category = response["content"]
    return category

def extract_agreement_date(summary: str):
    prompt = agreement_date_prompt(summary = summary)
    response = refine_response(prompt)
    agreement_date = response["content"]
    validated_date = validate_agreement_date(agreement_date)
    return validated_date

def extract_expiration_date(summary: str):
    prompt = expiration_date_prompt(summary = summary)
    response = refine_response(prompt)
    content = response["content"]
    content = re.sub("\W", " ", content)
    entity = duckling_time_entity(content)
    return entity

def extract_renewal_date(summary: str):
    prompt = renewal_date_prompt(summary = summary)
    response = refine_response(prompt)
    content = response["content"]
    content = re.sub("\W", " ", content)
    entity = duckling_time_entity(content)
    return entity

def extract_contract_value(summary: str):
    prompt = contract_value_prompt(summary = summary)
    response = refine_response(prompt)
    content = response["content"]
    value = duckling_money_entity(content)
    return value

def llm_based_extraction_result(summary: str):
    parties = extract_parties(summary)
    category = extract_category(summary)
    agreement_date = extract_agreement_date(summary)
    expiration_date = extract_expiration_date(summary)
    renewal_date = extract_renewal_date(summary)
    contract_value = extract_contract_value(summary)
    expire_date = compute_expiration_date(agreement_date, expiration_date)
    renew_date = compute_renewal_date(agreement_date, renewal_date)
    
    return {
        "category": category,
        "parties": parties,
        "value": contract_value,
        "agreement_date": agreement_date,
        "expiration_date": expire_date,
        "renewal_date": renew_date
    }
    
def embeddings(text:str):
    response = openai.Embedding.create(model = "text-embedding-ada-002",
                                      input = text)
    vector = response["data"][0]["embedding"]
    return vector

def search_summary_index(prompt: str):
    message = [
        {"role": "system", "content":SYSTEM_MESSAGE},
        {"role": "user", "content": prompt}
    ]
    completion = openai.ChatCompletion.create(model = "gpt-4",
                                              messages = message)
    return completion.choices[0].message

def process_contract(doc: str):
    text = " ".join(doc.split()[:5000])
    prompt = summary_section_prompt(text)
    resp = search_summary_index(prompt)
    summary = resp["content"]
    summary_vector = embeddings(summary) 
    return text, summary, summary_vector
    
def keyword_semantic_search(query: str, db_connection: psycopg2.extensions.connection):
    query_emb = embeddings(query)
    query_emb = json.dumps(query_emb)
    keyword_semantic_sql = """
                                WITH data as (
                                                SELECT
                                                    id, doc_id, summary, summary_vector,
                                                    ts_rank_cd(keyword_vector, plainto_tsquery('english', %s)) AS rank
                                                FROM document
                                                ORDER BY rank
                                                DESC LIMIT 5
                                            )
                                SELECT 
                                    id, doc_id, summary, rank,
                                    1 - (summary_vector <=> %s) AS distance
                                FROM data
                                ORDER BY distance
                                DESC LIMIT 1;
                            """
                            
    params = (query, query_emb)
    cursor = db_connection.cursor()
    cursor.execute(keyword_semantic_sql, params)
    response = cursor.fetchall()
    return response




def current_file_status(db_connection: psycopg2.extensions.connection, doc_id: str = None,
                        url: str = None, status: str = "pending"):
    if doc_id and url:
        cursor = db_connection.cursor()
        cursor.execute(""" SELECT doc_id FROM doc_status WHERE doc_id = %s""", (doc_id,))
        id = cursor.fetchone()
        if id:
            cursor.execute(""" UPDATE doc_status SET status = %s WHERE doc_id = %s """, (status, doc_id))
            db_connection.commit()
        else:
            cursor.execute(""" INSERT INTO doc_status (doc_id, url, status) VALUES (%s, %s, %s) """, (doc_id, url, status))
            db_connection.commit()
        
        


def insert_processed_contract_db(db_payload: dict, db_connection: psycopg2.extensions.connection):
    metadata = json.dumps(db_payload.get("metadata"))
    summary_emb = json.dumps(db_payload.get("summary_vector"))
    summary = db_payload.get("summary")
    text = db_payload.get("text")
    doc_id = db_payload.get("doc_id")
    cursor = db_connection.cursor()
    cursor.execute("""INSERT INTO document (doc_id, raw_contract, summary, metadata, summary_vector) VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                     (doc_id, text, summary, metadata, summary_emb))
    fetch_id = cursor.fetchone()
    db_connection.commit()
    return fetch_id
    