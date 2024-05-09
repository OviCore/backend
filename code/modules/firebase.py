#https://firebase.google.com/docs/auth/admin/verify-id-tokens#python
import firebase_admin
from fastapi import APIRouter
from firebase_admin import auth
from firebase_admin import credentials

router = APIRouter()

default_app = firebase_admin.initialize_app()

def verify_firebase_token(token):
    try:
        # Initialize the app with a service account, granting admin privileges
        cred = credentials.Certificate("code/modules/ovicore-firebase-adminsdk.json")
        firebase_admin.initialize_app(cred)
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        return {"status": True, "uid": uid}
    except Exception as e:
        return {"status": False, "error": str(e)}
    finally:
        firebase_admin.delete_app(firebase_admin.get_app())

def get_firebase_user(uid):
    try:
        cred = credentials.Certificate("code/modules/ovicore-firebase-adminsdk.json")
        firebase_admin.initialize_app(cred)
        user = auth.get_user(uid)
        return {"status": True, "user": user}
    except Exception as e:
        return {"status": False, "error": str(e)}
    finally:
        firebase_admin.delete_app(firebase_admin.get_app())

@router.post("/verify_token/")
async def verify_token(token: str):
    return verify_firebase_token(token)

@router.post("/get_user/")
async def get_user(uid: str):
    return get_firebase_user(uid)

@router.get("/status/")
async def health():
    return {"status": default_app.name}

def add_firebase(app):
    app.include_router(router, prefix="/firebase", tags=["firebase"])

