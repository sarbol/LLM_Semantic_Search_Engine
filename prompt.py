import json
import os
import re


SYSTEM_MESSAGE = "You are assuming the role of a Legal Practioner.\
                    Your main objective is to review Agreement/Contract"


def extract_relevant_context_prompts(context):
    prompt = f"Using the context provided below\n\n\
                -------------------------------------------------------------------------\n\n\
                Context:\n\n\
                {context}\n\n\
                ---------------------------------------------------------------------------\n\n\
                Write a well coherent summary that defines each of these attributes listed below\n\n\
                1. Name of Parties involved in the Agreement\n\
                2. Roles of the Parties in the Agreement\n\
                3. Type or Category of Agreement\n\
                4. Agreement Date\n\
                5. Effective Date\n\
                6. Expiration Date or expiration condition of the agreement\n\
                7. Termination term of the agreement\n\
                8. Monetary Value of the agreement between the parties\n\
                9. Renewal Term of the Agreement\n\n\
                -----------------------------------------------------------------------------------\n\n\
                Ensure the summary draws only from the provided context.\
                The summary should contain only the details provided in the context\n\
                If the context does not provide any relevant information for any of the attributes above,\
                focus only the attributes with relevant information about them.\n\n\
                Revise your your summary, ensure it meets all criteria and it doesn't exceed 250 words"
    return prompt


def update_extracted_summary(summary: str = None, context: str = None):
    prompt = f"You have an opportunity to update the summary of an agreement between two or more parties\
                using the new provided context.\n\n\
                ----------------------------------------------------------------------------------------\n\n\
                Summary:\n\n\
                {summary}\n\
                -----------------------------------------------------------------------------------------\n\n\
                New Context:\n\n\
                {context}\n\
                --------------------------------------------------------------------------------------------\n\n\
                Disregard any information that is not relevant to any of the summary attributes listed below\n\n\
                1. Name of Parties involved in the Agreement\n\
                2. Roles of the Parties in the Agreement\n\
                3. Type or Category of Agreement\n\
                4. Agreement Date\n\
                5. Effective Date\n\
                6. Expiration Date or expiration condition of the agreement\n\
                7. Termination term of the agreement\n\
                8. Monetary Value of the agreement between the parties\n\
                9. Renewal Term of the Agreement\n\n\
                ---------------------------------------------------------------------------------------------\n\n\
                Use the information in the new provided context to enrich the existing summary.\n\
                Add new relevant information to each attribute.\n\
                Disregard redundant information already provided in the existing summary.\n\
                Ensure the updated summary is not more than 500 words\n\
                Do not include any additional information not relevant to any of the 9 attributes listed above"
    return prompt


def parties_prompt(summary: str = None):
    
    prompt = f"""
                Consider the context below
                Context:
                {summary}
                ------------------------------------------------------------------------------
                In a JSON format, generate a Key:value Pair. Where each key is a party involved in the agreement
                and the value is the role of the party in the agreement.
                Summarize the role of the party using maximum of 3 words.
                if the role of a party can't be deduced from the given context, return Null
    """
    
    return prompt


def category_prompt(summary:str = None):
    
    prompt = f"""
                Consider the context below
                Context:
                {summary}
                --------------------------------------------------------------------------------------
                Extract in at most 3 words, the category of the agreement between the parties
                
    """
                
    return prompt


def agreement_date_prompt(summary: str = None):
    prompt = f"""
                Consider the context below
                Context:
                {summary}
                -------------------------------------------------------------------------------------
                Your objective is to extract in one word, the agreement date between the parties.
                Return only the date using (dd-mm-YYYY) format.
                if the context does not provide the agreement date. Return Null
    """
    
    return prompt


def expiration_date_prompt(summary: str = None):
    prompt = f"""
                Consider the context below
                Context:
                {summary}
                ---------------------------------------------------------------------------------------
                Your objective is to summarize in one sentence not more than 10 words, the expiration term of the
                agreement. Ensure your summary speaks from a time perspective by including time entity mentioned
                in the agreement. Try to extract time related entity.
    """
    
    return prompt


def contract_value_prompt(summary: str = None):
    prompt = f"""
            Consider the context below
            Context:
            {summary}
            ---------------------------------------------------------------------------------------------
            Your objective is to extract the monetary value of the agreemnet between the parties.
            Extracting only monetary entity from the provided context would be the most ideal.
            use less than 10 words.
    """
    
    return prompt


def renewal_date_prompt(summary: str = None):
    prompt = f"""
            Consider the context below
            Context:
            {summary}
            ------------------------------------------------------------------------------------------------
            Your objective is to extract the renewal time of the agreement.
            Extract only the time entity that describes when the contract automatically renews
            ignore any termination condition surrounding the renewal.
            Your output should be less than 10 words.
    """
    
    return prompt



def summary_section_prompt(context: str):
    prompt = f"""
                Carefully read the context below.
                Context:
                {context}
                _______________________________________________________________________________________________
                Your objective is to summarize the context into paragraphs explaining different ideas.
                You are to identify and summarize sections of the agreement relating to terms, clauses
                and conditions binding the parties.
                Where possiible, ensure you include all information relating to Name of Parties involved in the agreement,
                location, dates, contract values, numbers.
                Ensure each paragraph is monolithic, coherent and only expresses an idea.
                Ensure the dates are completely and accurately stated as written in the context
                Only use the information provided in the context.
                Do not include information not provided in the given context.
                Ensure your summary is concise, compact and accurate.
                Your output should be a well structured list of ideas.
                Only include the information the context provided in your output.
    """
    
    return prompt


