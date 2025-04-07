
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
# import jwt
from jose import jwt, JWTError
import asyncio
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from core.config import settings

client=AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
database=client['MONGODB_DATABASE']
users_collection=database['users']

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/auth", tags=["auth"])

class UserModel(BaseModel):
    username: str
    email: str
    full_name: str
    password: str


class UserInDB(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str

    
pwd_context=CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)

def get_password_hash(password):
    return pwd_context.hash(password)


def create_acces_token(data:dict, expires_delta:timedelta):
    to_encode=data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register")
async def register_user(user:UserModel):
    existing_user=await users_collection.find_one({"username":user.username})
    if existing_user:
        raise HTTPException(status_code=400,detail="User already exists")
    hashed_pass=get_password_hash(user.password)
    user_data={
        "username":user.username,
        "email":user.email,
        "full_name":user.full_name,
        "hashed_password":hashed_pass
    }
    new_user=await users_collection.insert_one(user_data)
    return {"Message":"User Registered successfully", "id":str(new_user.inserted_id)}

async def authenticate_user(username:str, password:str):
    user=await users_collection.find_one({"username":username})
    if not user or not verify_password(password, user['hashed_password']):
        return None
    return UserInDB(id=str(user['_id']), **user)
# {
#   "Message": "User Registered successfully",
#   "id": "67e02072138af0dd2580f68a"
# }

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_acces_token({"sub": user.username},  expires_delta=timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyb2NrIiwiZXhwIjoxNzQyNzQzOTE3fQ.BPKonl_thBBNERsMcfqnYl_KN66go_3UzMtjGNBqZ_c",
#   "token_type": "bearer"
# }

async def get_current_user(token:str=Depends(oauth2_scheme)):
    try:
        payload=jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM])
        username:str=payload.get('sub')
        if not username:
            raise HTTPException(status_code=401,detail="Invalid authentication")
        user=await users_collection.find_one({'username':username})
        if not user:
            raise HTTPException(status_code=401,detail="User not found")
        return UserInDB(id=str(user["_id"]), **user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

@router.get("/test")
async def test(current_user:str=Depends(get_current_user)):
    return {"message": "User endpoint working"}

