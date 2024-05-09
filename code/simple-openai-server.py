from typing import Annotated
import os
from fastapi import Depends, HTTPException, FastAPI, File, UploadFile, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.openapi.utils import get_openapi
from pymongo import MongoClient

##################################
# Custom modules
# - Environment variables
from modules.load_env import load_apikey_env
# - OpenAPI response and payload definition
from modules.apis_response_format import Health, Get_openai_text, Get_openai_text_file
from modules.apis_payload_format import Openai_simple_text, Openai_simple_prompt, Openai_question
from modules.html_converter import html_to_text
from modules.image_upload import upload_image_to_s3

# - AI
from modules.openai_access import get_simple_text, get_text_with_prompt

from typing import Any

from modules.mongo_operations import add_user_routes

##################################
# Set basic auth as security
security = HTTPBasic()
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    data, verification = load_apikey_env()
    apikey = data["APIKEY"]
    user = data["USER"]
  
    if ((credentials.username != user) or (credentials.password != apikey)):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED,
                            detail="incorrect user or apikey",
                            headers={"WWW-Authenticate":"Basic"})    
    return credentials.username

##################################
# Create APIs
app = FastAPI(dependencies=[Depends(authenticate)])

# Database MongoDB
def create_mongo_client():
    client = MongoClient(os.environ.get("DATABASE_URL"))
    return client

def get_database(client, db_name):
    db = client[db_name]
    return db

def get_collection(db, collection_name):
    collection = db[collection_name]
    return collection

client = create_mongo_client()
db = get_database(client, "openai")
collection = get_collection(db, "users")

add_user_routes(app, "openai", "users")
##################################
# Endpoints
@app.get("/")
def root_show_configuration_status():
    """
    This endpoint verifies the configuration status of the application.
    """
    config, validation = load_apikey_env()
    if (validation):
        status = "configured"
    else:
        status = "unconfigured"
    return{"status": status}

@app.get("/health", response_model=Health) 
def provide_health_status() -> Any:
    """
    This endpoint implements the health status to enable that the application runs on a container management platform like Kubernetes.
    """
    return { "status": "ok"}

@app.post("/get_openai_text/", response_model=Get_openai_text)
async def get_openai_text(openai_simple_text: Openai_simple_text) -> Any:
    """
    This endpoint sends an unformated text a prompt to OpenAI. 
    """

    print(f"***DEBUG: input text: {openai_simple_text.text}")

    text, validation = get_simple_text(openai_simple_text.text)
    print(f"***DEBUG: output text: {text}")
    
    if (validation["status"] == True):
        result = { "result": text }
        return { "text": result , "validation":  {"status" : str(validation["status"])}}
    else:
        result = { "result": text }
        print(f"***DEBUG: else (get_openai_text): {result}: {validation}")
        return { "text": result , "validation":  {"status" : str(validation["status"])}}

@app.post("/get_openai_text_with_prompt/", response_model=Get_openai_text)
async def get_openai_text_with_prompt(openai_simple_prompt: Openai_simple_prompt) -> Any:
    """
    This endpoint sends a prompt to OpenAI. This prompt is configured by the environment variable `OPENAI_PROMPT` by using the variables `<<CONTEXT>>` and `<<QUESTION>>`.
    """

    print(f"***DEBUG: context: {openai_simple_prompt.context}")
    print(f"***DEBUG: question: {openai_simple_prompt.question}")

    text, validation = get_text_with_prompt(openai_simple_prompt.context,openai_simple_prompt.question)
    print(f"***DEBUG: output text: {text}")
    
    if (validation["status"] == True):
        result = { "result": text }
        return { "text": result , "validation":  {"status" : str(validation["status"])}}
    else:
        result = { "result": text }
        print(f"***DEBUG: else (get_text_with_prompt): {result}: {validation}")
        return { "text": result , "validation":  {"status" : str(validation["status"])}}

@app.post("/get_openai_html_file_with_prompt/", response_model=Get_openai_text_file)
async def get_openai_html_file_with_prompt(   file: Annotated[UploadFile, File(description="A file as context for the question")],
                                               question: Annotated[str, Form()]) -> Any:
    """
    This endpoint sends a prompt to OpenAI. This prompt is configured by the environment variable `OPENAI_PROMPT` by using the variables `<<CONTEXT>>` and `<<QUESTION>>`.
    The context in the extracted plain text of uploaded html file and the question is the question parameter.
    """
    
    html_content =  await file.read()
    context_text, html_verification = html_to_text(html_content)
   
    print(f"***DEBUG: context_text: {context_text}")

    if html_verification == True:
        text, validation = get_text_with_prompt(str(context_text),question)
        print(f"***DEBUG: get_text_with_prompt text: {text}")   
        if (validation["status"] == True):
            result = { "result": text, "filename": file.filename }
            return { "text": result , "validation":  {"status" : str(validation["status"])}}
        else:
            result = { "result": text , "filename": file.filename}
            print(f"***DEBUG: else (get_openai_html_file_with_prompt): {result}: {validation}")
            return { "text": result , "validation":  {"status" : str(validation["status"])}}
    else:
            result = { "result": context_text , "filename": file.filename}
            print(f"***DEBUG: else (html_to_text): {result}")
            return { "text": result , "validation":  { "status" : "false"}}


@app.post("/get_openai_file_with_prompt/", response_model=Get_openai_text_file)
async def get_openai_file_with_prompt(   file: Annotated[UploadFile, File(description="A file as context for the question")],
                                question: Annotated[str, Form()]) -> Any:
    """
    This endpoint sends a prompt to OpenAI. This prompt is configured by the environment variable `OPENAI_PROMPT` by using the variables `<<CONTEXT>>` and `<<QUESTION>>`.
    The context in the unformated content of the uploaded file.
    """  
    context =  await file.read()
    text, validation = get_text_with_prompt(str(context),question)
    print(f"***DEBUG: output text: {text}")
    
    if (validation["status"] == True):
        result = { "result": text, "filename": file.filename }
        return { "text": result , "validation":  {"status" : str(validation["status"])}}
    else:
        result = { "result": text , "filename": file.filename}
        print(f"***DEBUG: else (get_openai_text): {result}: {validation}")
        return { "text": result , "validation":  {"status" : str(validation["status"])}}
    
@app.post("/upload_image_to_s3/")
async def upload_image_to_s3_endpoint(file: UploadFile = File(...)) -> Any:
    """
    This endpoint uploads an image file to S3.
    """
    message, status = upload_image_to_s3(file)
    return { "status": status, "message": message }

@app.get("/test_mongodb")
async def test_mongodb():
    document = collection.find_one()
    # Convert ObjectId to string
    if document and "_id" in document:
        document["_id"] = str(document["_id"])
    return {"first_document": document}

##################################
# OpenAPI configuration for swagger UI

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Ovicore Technologies - OpenAI Integration",
        version="1.0.0",
        #openapi_version="3.1.0",
        summary="OpenAPI v3.1.0",
        description="Backend service for OpenAI integration for the Ovicore Technologies apps.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="localhost",port=8080)