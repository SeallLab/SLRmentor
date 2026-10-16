from dotenv import load_dotenv
load_dotenv()
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_pymongo import PyMongo
import os, json, datetime
import helpers.scholarlyapi as sa #This is for querying and getting paper abstracts
import helpers.cryptographic_helpers as ch #Generating chat hashes
from helpers.llm.promptBuilder import Prompt #for building prompts
import helpers.llm.llmPromptingUtils as pu #for actually calling the AI API
from helpers.RAG.RetrieverManager import RetrieverManager
from helpers.db.mongodbhelpers import MongoHelper
from helpers.llm.llmReturnFormat import Response


# from google.genai.types import HttpOptions



app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
mh = MongoHelper(mongo)
CORS(app)

hash_byte_length = 16
chat_hash_length = 8
message_history_limit = 30
RAG_doc_limit = 30
gemini_key = os.getenv('GEMINI_API_KEY')
gpt_key = os.getenv('GPT_API_KEY')
rm = RetrieverManager(
    mongo_uri=os.getenv("MONGO_URI"),
    namespace="SLRMentor.document_rag",
    index_name="vector_index",
    top_k=RAG_doc_limit
)


@app.route("/", methods=['GET'])
def test():
    return "Server is live ;)"


@app.route("/createchat", methods=['POST'])
def create_chat():
    return_request = {
        "hash": "",
        "status": False,
        "message": "whoops, something went wrong"
    }
    status_code = 401

    try:
        
        hash = ch.generate_hash(hash_byte_length, chat_hash_length)
    
        #check if generated hash already exists in db
        existing = mongo.db.search_string_chats.find_one({"_id": hash})
        if existing:
            raise ValueError("whoops, something went wrong. Try creating a new chat again")

        
        #create new messege history related to the hash in db
        new_search_string_chat = {
            "_id": hash,  
            "chat_creation_date": datetime.datetime.now(),
            "chat_last_use": datetime.datetime.now(),
            "chat_history": [],
            "message_count": 0,
            "current_search_string": "",
            "current_search_string_format": ""
        }

        new_creteria_chat = {
            "_id": hash,  
            "chat_creation_date": datetime.datetime.now(),
            "chat_last_use": datetime.datetime.now(),
            "chat_history": [],
            "message_count": 0,
            "current_criteria": "",
        }
        
        new_mentor_chat = {
            "_id": hash,  
            "chat_creation_date": datetime.datetime.now(),
            "chat_last_use": datetime.datetime.now(),
            "chat_history": [],
            "message_count": 0,
        }
        
        new_system_context = {
            "_id": hash,  
            "chat_creation_date": datetime.datetime.now(),
            "chat_last_use": datetime.datetime.now(),
            "system_context": "",
        }
        
        mongo.db.search_string_chats.insert_one(new_search_string_chat)
        mongo.db.criteria_chats.insert_one(new_creteria_chat)
        mongo.db.mentor_chats.insert_one(new_mentor_chat)
        mongo.db.system_context.insert_one(new_system_context)
        
        #update return request with correct info
        return_request["hash"] = hash
        return_request["status"] = True
        return_request["message"] = "Succesfully generated new chat"
        status_code = 200
        
    except Exception as e:
        print(e)
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code

@app.route("/getsystemcontext", methods=['POST'])
def get_system_context():
    
    request_required_fields = ["hash_plain_text"]
    return_request = {
        "status": False,
        "message": "",
        "system_context": ""
        
    } 
    status_code = 401
    try:
        
        #validate that all required fields are present in request
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
             
            raise ValueError("request missing fields")

        #validate hash exists
        hash = data["hash_plain_text"]
        chat_doc = mongo.db.system_context.find_one({"_id": hash})
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")
        
        
        return_request["system_context"] = chat_doc["system_context"]
        return_request["message"] = "Succesfully retireved messsage histoy"
        return_request["status"] = True
        status_code = 200
        
    except Exception as e:
        print(e)
        status_code = 500
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code
        
@app.route("/getchathistory", methods=['POST'])
def get_chat_history():
    
    request_required_fields = ["hash_plain_text"]
    return_request = {
        "status": False,
        "message": "",
        "message_count": None,
        "chat_history": [],
        
    } 
    status_code = 401
    try:
        
        #validate that all required fields are present in request
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
             
            raise ValueError("request missing fields")

        #validate hash exists
        hash = data["hash_plain_text"]
        chat_doc = mongo.db.search_string_chats.find_one({"_id": hash})
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")
        
        
        #get chat
        #print(chat_doc)
        return_request["chat_history"] = chat_doc["chat_history"]
        return_request["message_count"] = chat_doc["message_count"]
        return_request["message"] = "Succesfully retireved messsage histoy"
        return_request["status"] = True
        status_code = 200
        
    except Exception as e:
        print(e)
        status_code = 500
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code

@app.route("/getcriteriachathistory", methods=['POST'])
def get_criteria_chat_history():
    
    request_required_fields = ["hash_plain_text"]
    return_request = {
        "status": False,
        "message": "",
        "message_count": None,
        "chat_history": [],
        
    } 
    status_code = 401
    try:
        
        #validate that all required fields are present in request
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
             
            raise ValueError("request missing fields")

        #validate hash exists
        hash = data["hash_plain_text"]
        chat_doc = mongo.db.criteria_chats.find_one({"_id": hash})
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")
        
        
        #get chat
        #print(chat_doc)
        return_request["chat_history"] = chat_doc["chat_history"]
        return_request["message_count"] = chat_doc["message_count"]
        return_request["message"] = "Succesfully retireved messsage histoy"
        return_request["status"] = True
        status_code = 200
        
    except Exception as e:
        print(e)
        status_code = 500
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code
    
@app.route("/getmentorchathistory", methods=['POST'])
def get_mentor_chat_history():
    
    request_required_fields = ["hash_plain_text"]
    return_request = {
        "status": False,
        "message": "",
        "message_count": None,
        "chat_history": [],
        
    } 
    status_code = 401
    try:
        
        #validate that all required fields are present in request
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
             
            raise ValueError("request missing fields")

        #validate hash exists
        hash = data["hash_plain_text"]
        chat_doc = mongo.db.mentor_chats.find_one({"_id": hash})
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")
        
        
        #get chat
        #print(chat_doc)
        return_request["chat_history"] = chat_doc["chat_history"]
        return_request["message_count"] = chat_doc["message_count"]
        return_request["message"] = "Succesfully retireved messsage histoy"
        return_request["status"] = True
        status_code = 200
        
    except Exception as e:
        print(e)
        status_code = 500
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code

@app.route("/setsystemcontext", methods=['POST'])
def set_system_context():
    
    request_required_fields = ["hash_plain_text", "system_context"]
    return_request = {
        "status": False
    }
    status_code = 401
    try:
        
        #validate that all required fields are present in request
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
             
            raise ValueError("request missing fields")

        #validate hash exists
        hash = data["hash_plain_text"]
        chat_doc = mongo.db.system_context.find_one({"_id": hash})
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")
        # Update the system context
        mongo.db.system_context.update_one(
            {"_id": hash},
            {
                "$set": {
                    "system_context": data["system_context"],
                    "chat_last_use": datetime.datetime.now(),
                }
            }
        )
        
        #finalize finished return json
        return_request["status"] = True
        status_code = 200
        #return the llm respnse to the user
    except Exception as e:
        print(e)
        status_code = 500
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code
        
@app.route("/prompt", methods=['POST'])
def prompt():
    
    request_required_fields = ["hash_plain_text", "user_message"]
    return_request = {
        "status": False,
        "ai_used": "",
        "user_message": "",
        "llm_response": "",
        "updated_search_string": ""
    }
    status_code = 401
    try:
        
        #validate that all required fields are present in request
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
             
            raise ValueError("request missing fields")

        #validate hash exists
        hash = data["hash_plain_text"]
        chat_doc = mongo.db.search_string_chats.find_one(
            {"_id": hash},
            {"chat_history": 0}
        )
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")

        current_search_string = chat_doc.get("current_search_string", "")
        current_search_string_format = chat_doc.get("current_search_string_format", "")
        #system context retrieval
        chat_doc2 = mongo.db.system_context.find_one({"_id": hash})
        if not chat_doc2:
            raise ValueError("Chat with given hash doesnt exsist")
        sys_context = chat_doc2.get("system_context", "")
        #RAG
        top_docs = rm.get_relevant_documents_safe(data["user_message"])
        formatted_docs = rm.format_docs(top_docs)
        rag_context_formated_docs = rm.format_docs_prompt(formatted_docs, prescript="Contex", count=1)
        
        #Flow chart the type of prompt, is this the research question or a followup?(check db current search string field)
        paper_context = ""
        base_prompt = ""
        # Read all prompt components using UTF-8 to prevent decode issues
        with open("helpers/llm/prompts/searchstrings/identifyingKeyWordsPrompt.txt", "r", encoding="utf-8") as f:
            identify_kw_prompt = f.read()

        with open("helpers/llm/prompts/searchstrings/userInputPrompt.txt", "r", encoding="utf-8") as f:
            user_input_prompt = f.read()

        with open("helpers/llm/prompts/searchstrings/specificationFollowup.txt", "r", encoding="utf-8") as f:
            end_specification = f.read()
        

        user_input = f'User Input: {data["user_message"]} \n \n'
        if current_search_string.strip() == "":
            with open("helpers/llm/prompts/searchstrings/baseQuestionPrompt.txt", "r", encoding="utf-8") as f:
                base_prompt = f.read()
            paper_context = ""
            current_search_string_format = "General"
        else:
            with open("helpers/llm/prompts/searchstrings/baseFollowupPrompt.txt", "r", encoding="utf-8") as f:
                base_prompt = f.read()

            paper_context = f'Current search string: {current_search_string} \n \n'
            with open("helpers/llm/prompts/conversion/3_formatContext.txt", "r", encoding="utf-8") as f:
                user_input_context = f.read()
            with open("helpers/llm/prompts/conversion/" + str(valid_ss_conversions.get(current_search_string_format, valid_ss_conversions["General"])), "r", encoding="utf-8") as f:
                current_format = f.read()
            paper_context = paper_context + user_input_context + current_format

            abstracts = sa.get_abstracts_semantic_scholar(5, current_search_string)
            if isinstance(abstracts, str): #if there was no error getting the abstracts
                paper_context = paper_context + f'\n \nHere is the tittles and abstracts returned by the current search string for context: \n' + abstracts 

        chat_history_str = mh.get_chat_history_as_string("search_string_chats", message_history_limit, hash)
        chat_history_str = "\n\nRecent Message History:\n" + chat_history_str + "\nEnd of Recent Message History\n\n"
        rag_context = "The following is some relevant context and information in no perticular order to help you answer the users question: \n" + "\n".join(rag_context_formated_docs) + "\n\n"
        paper_context = rag_context + paper_context
        paper_context = f' Users SLR Context: {sys_context} \n\n' + paper_context
        
        prompt = Prompt()
        prompt.append_item(base_prompt)
        prompt.append_item(paper_context)
        prompt.append_item(identify_kw_prompt)
        prompt.append_item(user_input_prompt)
        prompt.append_item(chat_history_str)
        prompt.append_item(user_input)
        prompt.append_item(end_specification)
        full_prompt = prompt.get_prompt_as_str()
        
        print(full_prompt)
        #callin llm
        llm_response = {}
        ai_used = ""
        try:
            llm_response = pu.call_gemini(gemini_key, full_prompt)
            ai_used = "Gemini"

        except Exception as e:
            print(f"Gemini call failed, falling back to ChatGPT: {e}")
            llm_response = pu.call_chatgpt(gpt_key, full_prompt)
            ai_used = "chatGPT"


            

        updated_search_string = llm_response["updated_search_string"]
        if not llm_response["has_changed"]:
            updated_search_string = current_search_string
        
        #create new message to store in db
        new_db_message = {
            "user_message": data["user_message"],
            "llm_response": llm_response["text"],
            "message_dt": datetime.datetime.now(),
            "message_number": int(chat_doc["message_count"]) + 1,
            "search_string": updated_search_string,  
            "search_string_format": current_search_string_format
        }
        
        # Update the chat document: push new message, update message count and last use
        mongo.db.search_string_chats.update_one(
            {"_id": hash},
            {
                "$push": {"chat_history": new_db_message},
                "$set": {
                    "chat_last_use": datetime.datetime.now(),
                    "message_count": int(chat_doc["message_count"]) + 1,
                    "current_search_string": updated_search_string,
                    "current_search_string_format": current_search_string_format
                }
            }
        )
        
        
        
        #finalize finished return json
        return_request["llm_response"] = llm_response["text"]
        return_request["user_message"] = data["user_message"]
        return_request["updated_search_string"] = updated_search_string
        return_request["ai_used"] = ai_used
        return_request["status"] = True
        status_code = 200
        #return the llm respnse to the user
    except Exception as e:
        print(e)
        status_code = 500
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code
    
    
def check_missing_or_blank_fields(data, request_required_fields):
    '''returns true if a field is missing or is blank in the data json given from request'''
    if any(field not in data or data.get(field) in ["", None] for field in request_required_fields):
        return True
    return False

valid_ss_conversions = {"General":"4_generalformat.txt", "IEEE Xplore":"4_ieeeXploreformat.txt", "Google Scholar":"4_googlescholarformat.txt"}
@app.route("/conversionformats", methods=['GET'])
def get_conversionformats():
    return_request = {
        "formats": valid_ss_conversions.keys()
    }
    return return_request


@app.route("/convertsearchstring", methods=["POST"])
def convert():
    request_required_fields = ["hash_plain_text", "conversion_format"]

    return_request = {
        "status": False,
        "ai_used": "",
        "user_message": "",
        "llm_response": "",
        "updated_search_string": "",
        "current_format": "",
        "message": "",
    }

    try:
        # -------------------------------------------------
        # 1. Validate request body
        # -------------------------------------------------
        data = request.get_json(silent=True)

        if not data:
            return_request["message"] = "Request body must be valid JSON"
            return jsonify(return_request), 400

        if check_missing_or_blank_fields(data, request_required_fields):
            return_request["message"] = "Request missing required fields"
            return jsonify(return_request), 400

        hash_plain_text = str(data["hash_plain_text"]).strip()
        requested_conversion_format = str(data["conversion_format"]).strip()

        if requested_conversion_format not in valid_ss_conversions:
            return_request["message"] = "Conversion search string format not recognized"
            return jsonify(return_request), 400

        # -------------------------------------------------
        # 2. Retrieve existing search string chat from DB
        # -------------------------------------------------
        chat_doc = mongo.db.search_string_chats.find_one(
            {"_id": hash_plain_text},
            {"chat_history": 0}
        )

        if not chat_doc:
            return_request["message"] = "Chat with given hash does not exist"
            return jsonify(return_request), 404

        current_search_string = chat_doc.get("current_search_string", "")
        current_search_string_format = str(
            chat_doc.get("current_search_string_format", "")
        ).strip()

        if not current_search_string:
            return_request["message"] = "Current search string is empty"
            return jsonify(return_request), 500

        if current_search_string_format not in valid_ss_conversions:
            return_request["message"] = "Current search string format not recognized"
            return jsonify(return_request), 500

        if requested_conversion_format == current_search_string_format:
            return_request["message"] = (
                "Conversion format must be different than current format"
            )
            return jsonify(return_request), 400

        # -------------------------------------------------
        # 3. Load prompt files
        # -------------------------------------------------
        try:
            with open(
                "helpers/llm/prompts/conversion/1_BasePrompt.txt",
                "r",
                encoding="utf-8"
            ) as f:
                base_prompt = f.read()

            with open(
                "helpers/llm/prompts/conversion/2_userInputPrompt.txt",
                "r",
                encoding="utf-8"
            ) as f:
                user_input_prompt = f.read()

            with open(
                "helpers/llm/prompts/conversion/3_formatContext.txt",
                "r",
                encoding="utf-8"
            ) as f:
                user_input_context = f.read()

            current_format_filename = valid_ss_conversions[current_search_string_format]
            with open(
                "helpers/llm/prompts/conversion/" + str(current_format_filename),
                "r",
                encoding="utf-8"
            ) as f:
                current_format = f.read()

            with open(
                "helpers/llm/prompts/conversion/5_conversionContext.txt",
                "r",
                encoding="utf-8"
            ) as f:
                convert_to_context = f.read()

            convert_to_format_filename = valid_ss_conversions[requested_conversion_format]
            with open(
                "helpers/llm/prompts/conversion/" + str(convert_to_format_filename).strip(),
                "r",
                encoding="utf-8"
            ) as f:
                convert_to_format = f.read()

            with open(
                "helpers/llm/prompts/conversion/specificationFollowup.txt",
                "r",
                encoding="utf-8"
            ) as f:
                end_specification = f.read()

        except FileNotFoundError as e:
            print(f"Prompt file missing: {e}")
            return_request["message"] = f"Prompt file missing: {e}"
            return jsonify(return_request), 500

        except Exception as e:
            print(f"Error loading prompt files: {e}")
            return_request["message"] = f"Error loading prompt files: {e}"
            return jsonify(return_request), 500

        # -------------------------------------------------
        # 4. Build full prompt
        # -------------------------------------------------
        search_string = f"User Input: {current_search_string}\n\n"

        prompt = Prompt()
        prompt.append_item(base_prompt)
        prompt.append_item(user_input_prompt)
        prompt.append_item(search_string)
        prompt.append_item(user_input_context)
        prompt.append_item(current_format)
        prompt.append_item(convert_to_context)
        prompt.append_item(convert_to_format)
        prompt.append_item(end_specification)

        full_prompt = prompt.get_prompt_as_str()

        # -------------------------------------------------
        # 5. Call AI with Gemini -> ChatGPT fallback
        # -------------------------------------------------
        try:
            llm_response, ai_used = pu.call_ai_with_fallback(
                gemini_key=gemini_key,
                gpt_key=gpt_key,
                prompt=full_prompt,
                schema=Response,
            )

        except Exception as e:
            print(f"All AI providers failed in /convertsearchstring: {e}")
            return_request["message"] = str(e)
            return jsonify(return_request), 502

        # -------------------------------------------------
        # 6. Validate AI response
        # -------------------------------------------------
        if not isinstance(llm_response, dict):
            return_request["message"] = "AI response was not a dictionary"
            return jsonify(return_request), 502

        llm_text = str(llm_response.get("text", "")).strip()
        updated_search_string = str(
            llm_response.get("updated_search_string", "")
        ).strip()

        if not llm_text:
            return_request["message"] = "AI response missing text"
            return jsonify(return_request), 502

        if not updated_search_string:
            return_request["message"] = "AI response missing updated_search_string"
            return jsonify(return_request), 502

        has_changed = llm_response.get("has_changed")

        if has_changed is None:
            return_request["message"] = "AI response missing has_changed"
            return jsonify(return_request), 502

        # -------------------------------------------------
        # 7. Store result in DB
        # -------------------------------------------------
        try:
            current_message_count = int(chat_doc.get("message_count", 0))
            new_message_count = current_message_count + 1

            user_message = (
                f"Convert the current search string to the "
                f"{requested_conversion_format} format"
            )

            new_db_message = {
                "user_message": user_message,
                "llm_response": llm_text,
                "message_dt": datetime.datetime.now(),
                "message_number": new_message_count,
                "search_string": updated_search_string,
                "search_string_format": requested_conversion_format,
            }

            mongo.db.search_string_chats.update_one(
                {"_id": hash_plain_text},
                {
                    "$push": {
                        "chat_history": new_db_message
                    },
                    "$set": {
                        "chat_last_use": datetime.datetime.now(),
                        "message_count": new_message_count,
                        "current_search_string": updated_search_string,
                        "current_search_string_format": requested_conversion_format,
                    },
                },
            )

        except Exception as e:
            print(f"Database update failed in /convertsearchstring: {e}")
            return_request["message"] = f"Database update failed: {e}"
            return jsonify(return_request), 500

        # -------------------------------------------------
        # 8. Return success response
        # -------------------------------------------------
        return_request["status"] = True
        return_request["ai_used"] = ai_used
        return_request["user_message"] = user_message
        return_request["llm_response"] = llm_text
        return_request["updated_search_string"] = updated_search_string
        return_request["current_format"] = requested_conversion_format
        return_request["message"] = "Search string converted successfully"

        return jsonify(return_request), 200

    except Exception as e:
        print(f"Unexpected error in /convertsearchstring: {e}")
        return_request["message"] = f"Unexpected server error: {e}"
        return jsonify(return_request), 500


@app.route("/criteria", methods=['POST'])
def criteria():
    
    request_required_fields = ["hash_plain_text", "user_message"]
    return_request = {
        "status": False,
        "ai_used": "",
        "user_message": "",
        "llm_response": "",
        "updated_criteria": ""
    }
    status_code = 401
    try:
        
        #validate that all required fields are present in request
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):   
            raise ValueError("request missing fields")

        #validate hash exists
        hash = data["hash_plain_text"]
        chat_doc = mongo.db.criteria_chats.find_one(
            {"_id": hash},
            {"chat_history": 0}
        )
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")

        current_criteria = chat_doc.get("current_criteria", "")        
        
        chat_doc2 = mongo.db.system_context.find_one({"_id": hash})
        if not chat_doc2:
            raise ValueError("Chat with given hash doesnt exsist")
        sys_context = chat_doc2.get("system_context", "")
        #RAG
        top_docs = rm.get_relevant_documents_safe(data["user_message"])
        formatted_docs = rm.format_docs(top_docs)
        rag_context_formated_docs = rm.format_docs_prompt(formatted_docs, prescript="Contex", count=1)
        
        #Flow chart the type of prompt, is this the research question or a followup?(check db current search string field)
        paper_context = ""
        base_prompt = ""
        # Read all prompt components using UTF-8 to prevent decode issues
        with open("helpers/llm/prompts/criteria/userInputPrompt.txt", "r", encoding="utf-8") as f:
            user_input_prompt = f.read()

        with open("helpers/llm/prompts/criteria/specificationFollowup.txt", "r", encoding="utf-8") as f:
            end_specification = f.read()
        

        user_input = f'User Input: {data["user_message"]} \n \n'
        if current_criteria.strip() == "":
            with open("helpers/llm/prompts/criteria/baseQuestionPrompt.txt", "r", encoding="utf-8") as f:
                base_prompt = f.read()
            paper_context = ""
        else:
            with open("helpers/llm/prompts/criteria/baseFollowupPrompt.txt", "r", encoding="utf-8") as f:
                base_prompt = f.read()
            paper_context = f"Current inclusion/exclusion criteria:\n{current_criteria}\n\n"

        chat_history_str = mh.get_chat_history_as_string("criteria_chats", message_history_limit, hash)
        chat_history_str = "\n\nRecent Message History:\n" + chat_history_str + "\nEnd of Recent Message History\n\n"
        rag_context = "The following is some relevant context and information in no perticular order to help you answer the users question: \n" + "\n".join(rag_context_formated_docs) + "\n\n"
        paper_context = rag_context + paper_context
        paper_context = f' Users SLR Context: {sys_context} \n\n' + paper_context
        prompt = Prompt()
        prompt.append_item(base_prompt)
        prompt.append_item(paper_context)
        prompt.append_item(user_input_prompt)
        prompt.append_item(chat_history_str)
        prompt.append_item(user_input)
        prompt.append_item(end_specification)
        full_prompt = prompt.get_prompt_as_str()
        print(full_prompt)
        #callin llm
        llm_response = {}
        ai_used = ""
        try:
            llm_response = pu.call_gemini_criteria(gemini_key, full_prompt)
            ai_used = "Gemini"

        except Exception as e:
            print(f"Gemini call failed, falling back to ChatGPT: {e}")
            llm_response = pu.call_chatgpt_criteria(gpt_key, full_prompt)
            ai_used = "chatGPT"

        updated_inclusion_exclusion_criteria = llm_response["updated_inclusion_exclusion_criteria"]
        if not llm_response["has_changed"]:
            updated_inclusion_exclusion_criteria = current_criteria
        
        #create new message to store in db
        new_db_message = {
            "user_message": data["user_message"],
            "llm_response": llm_response["text"],
            "message_dt": datetime.datetime.now(),
            "message_number": int(chat_doc["message_count"]) + 1,
            "criteria": updated_inclusion_exclusion_criteria,  
        }
        
        # Update the chat document: push new message, update message count and last use
        mongo.db.criteria_chats.update_one(
            {"_id": hash},
            {
                "$push": {"chat_history": new_db_message},
                "$set": {
                    "chat_last_use": datetime.datetime.now(),
                    "message_count": int(chat_doc["message_count"]) + 1,
                    "current_criteria": updated_inclusion_exclusion_criteria,
                }
            }
        )
        
        
        
        #finalize finished return json
        return_request["llm_response"] = llm_response["text"]
        return_request["user_message"] = data["user_message"]
        return_request["updated_criteria"] = updated_inclusion_exclusion_criteria
        return_request["ai_used"] = ai_used
        return_request["status"] = True
        status_code = 200
        #return the llm respnse to the user
    except Exception as e:
        print(e)
        status_code = 500
        return_request["message"] = str(e)
        
    finally:
        return jsonify(return_request), status_code
    
@app.route("/ragquery", methods=["POST"])
def rag_query():
    request_required_fields = ["user_message"]
    return_request = {
        "status": False,
        "message": "",
        "user_message": "",
        "top_documents": []
    }
    status_code = 401
    try:
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
            raise ValueError("Request missing required fields")

        user_message = data["user_message"]

        # Safely retrieve documents
        top_docs = rm.get_relevant_documents_safe(user_message)
        formatted_docs_plaintext = rm.format_docs(top_docs)

        return_request.update({
            "status": True,
            "message": "Successfully retrieved documents",
            "user_message": user_message,
            "top_documents": formatted_docs_plaintext
        })
        status_code = 200

    except Exception as e:
        print(e)
        return_request["message"] = str(e)
        status_code = 500

    finally:
        return jsonify(return_request), status_code

@app.route("/mentor", methods=["POST"])
def mentor():
    request_required_fields = ["hash_plain_text", "user_message"]
    return_request = {
        "status": False,
        "message": "",
        "user_message": "",
        "llm_response": "",
        "ai_used": ""
        }
    status_code = 401
    try:
        data = request.json
        if check_missing_or_blank_fields(data, request_required_fields):
            raise ValueError("Request missing required fields")

        hash = data["hash_plain_text"]
        user_message = data["user_message"]

        # Validate hash exists
        chat_doc = mongo.db.mentor_chats.find_one(
            {"_id": hash},
            {"chat_history": 0}
        )
        if not chat_doc:
            raise ValueError("Chat with given hash doesn't exist")
        
        chat_doc = mongo.db.search_string_chats.find_one(
            {"_id": hash},
            {"chat_history": 0}
        )
        #validate hash exists
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")
        #getting the current latest search string and format
        current_search_string = chat_doc.get("current_search_string", "")
        
        chat_doc = mongo.db.criteria_chats.find_one(
            {"_id": hash},
            {"chat_history": 0}
        )
        if not chat_doc:
            raise ValueError("Chat with given hash doesnt exsist")

        current_criteria = chat_doc.get("current_criteria", "") 
        
        chat_doc2 = mongo.db.system_context.find_one({"_id": hash})
        if not chat_doc2:
            raise ValueError("Chat with given hash doesnt exsist")
        sys_context = chat_doc2.get("system_context", "")
        
        # Safely retrieve documents
        top_docs = rm.get_relevant_documents_safe(user_message)
        formatted_docs = rm.format_docs(top_docs)
        rag_context_formated_docs = rm.format_docs_prompt(formatted_docs, prescript="Contex", count=1)
        
        #Flow chart the type of prompt, is this the research question or a followup?(check db current search string field)
        paper_context = ""
        base_prompt = ""
        # Read all prompt components using UTF-8 to prevent decode issues
        with open("helpers/llm/prompts/mentor/userInputPrompt.txt", "r", encoding="utf-8") as f:
            user_input_prompt = f.read()

        with open("helpers/llm/prompts/mentor/specificationFollowup.txt", "r", encoding="utf-8") as f:
            end_specification = f.read()
        

        user_input = f'User Input: {data["user_message"]} \n \n'
        
        with open("helpers/llm/prompts/mentor/baseQuestionPrompt.txt", "r", encoding="utf-8") as f:
            base_prompt = f.read()
            
        rag_context = "The following is some relevant context and information in no perticular order to help you answer the users question: \n" + "\n".join(rag_context_formated_docs) + "\n\n"
        paper_context = rag_context + f'Current search string: {current_search_string} \n \n' + f'Current inclusion/exclusion criteria:\n{current_criteria}\n\n'
        paper_context = f' Users SLR Context: {sys_context} \n\n' + paper_context
        chat_history_str = mh.get_chat_history_as_string("mentor_chats", message_history_limit, hash)
        chat_history_str = "\n\nRecent Message History:\n" + chat_history_str + "\nEnd of Recent Message History\n\n"
        
        prompt = Prompt()
        prompt.append_item(base_prompt)
        prompt.append_item(paper_context)
        prompt.append_item(user_input_prompt)
        prompt.append_item(chat_history_str)
        prompt.append_item(user_input)
        prompt.append_item(end_specification)
        full_prompt = prompt.get_prompt_as_str()
        print(full_prompt)
        
        llm_response = {}
        ai_used = ""
        try:
            llm_response = pu.call_gemini_mentor(gemini_key, full_prompt)
            ai_used = "Gemini"

        except Exception as e:
            print(f"Gemini call failed, falling back to ChatGPT: {e}")
            llm_response = pu.call_chatgpt_mentor(gpt_key, full_prompt)
            ai_used = "chatGPT"
            
        #create new message to store in db
        new_db_message = {
            "user_message": data["user_message"],
            "llm_response": llm_response["text"],
            "message_dt": datetime.datetime.now(),
            "message_number": int(chat_doc["message_count"]) + 1,
        }
        
        # Update the chat document: push new message, update message count and last use
        mongo.db.mentor_chats.update_one(
            {"_id": hash},
            {
                "$push": {"chat_history": new_db_message},
                "$set": {
                    "chat_last_use": datetime.datetime.now(),
                    "message_count": int(chat_doc["message_count"]) + 1,
                }
            }
        )    
        
        
        #finalize finished return json
        return_request["llm_response"] = llm_response["text"]
        return_request["user_message"] = data["user_message"]
        return_request["ai_used"] = ai_used
        return_request["status"] = True
        status_code = 200
        #return the llm respnse to the user
    except Exception as e:
        print(e)
        return_request["message"] = str(e)
        status_code = 500

    finally:
        return jsonify(return_request), status_code