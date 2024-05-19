from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from fastapi import HTTPException


from google.oauth2 import id_token
from google.auth.transport import requests

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(SessionMiddleware ,secret_key='maihoonjiyan')


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/auth")
def authentication(request: Request, token: str):
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        user = id_token.verify_oauth2_token(token, requests.Request(), "116988534719-0j3baq1jkp64v4ghen352a283t6anvr0.apps.googleusercontent.com")

        if user:
            request.session['user'] = {
                "email": user["email"]
            }
            return user['name'] + ' Logged In successfully'
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/') 
def check(request:Request): 
	user = request.session.get('user')
	if user is not None:
		return "hi "+ str(user['email'])
	else:
		return "User not found in session"
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)