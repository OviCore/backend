from fastapi import APIRouter
from pymongo import MongoClient
import os

router = APIRouter()

def add_user_routes(app, db_name, collection_name):
    client = MongoClient(os.environ.get("DATABASE_URL"))
    db = client[db_name]
    collection = db[collection_name]

    @router.post("/create_user/")
    async def create_user(email: str, password: str):
        db.command("createUser", email, pwd=password, roles=["readWrite"])

    @router.post("/insert_user/")
    async def insert_user(email: str, password: str):
        collection.insert_one({"email": email, "password": password})

    @router.get("/find_user/")
    async def find_user(email: str):
        user = collection.find_one({"email": email})
        return user

    @router.put("/update_user/")
    async def update_user(email: str, password: str):
        collection.update_one({"email": email}, {"$set": {"password": password}})

    @router.delete("/delete_user/")
    async def delete_user(email: str):
        collection.delete_one({"email": email})

    app.include_router(router, prefix="/user", tags=["user"])