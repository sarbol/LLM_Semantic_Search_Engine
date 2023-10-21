from helpers import llama_document_summary_index, llama_document_loader, llama_response, refine_response, load_query_engine
from llama_index import SimpleDirectoryReader
import os
import json
import pickle
from glob import glob
from helpers import *
from config import *





if __name__ == "__main__":
    file_path = "/Users/oladipoyusuf/Documents/CUAD_v1/full_contract_pdf/Part_III/Marketing/Zounds Hearing, Inc. - MANUFACTURING DESIGN MARKETING AGREEMENT.PDF"
    doc = SimpleDirectoryReader(input_files = [file_path],
                                required_exts = [".pdf", ".docx", ".DOCX"])
    doc = doc.load_data()
    summary = summary_index(doc)
    
    print(f"Doc Summary: {summary}")
    print("\n\n")
    result = llm_based_extraction_result(summary)
    print(result)
    
    
    # date_ = "Null"
    # print(infer_date_pattern(date_))
