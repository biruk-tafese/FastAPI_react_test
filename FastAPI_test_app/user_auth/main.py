from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing_extensions import Annotated

# Fake database with roles for users
fake_users_db = {
    "passenger1": {
        "username": "passenger1",
        "full_name": "Passenger One",
        "email": "passenger1@example.com",
        "hashed_password": "fakehashedpass1",
        "disabled": False,
        "role": "passenger"
    },
    "staff1": {
        "username": "staff1",
        "full_name": "Staff One",
        "email": "staff1@example.com",
        "hashed_password": "fakehashedstaff1",
        "disabled": False,
        "role": "staff"
    },
    "staff2": {
        "username": "staff2",
        "full_name": "Staff Two",
        "email": "staff2@example.com",
        "hashed_password": "fakehashedstaff2",
        "disabled": True,  # Disabled user
        "role": "staff"
    },
}

app = FastAPI()

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None
    role: str

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    # This doesn't provide any security at all
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_passenger(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if current_user.role != "passenger":
        raise HTTPException(status_code=403, detail="Access forbidden for non-passengers")
    return current_user

async def get_current_active_staff(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Access forbidden for non-staff")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

# Endpoint accessible only by passengers
@app.get("/passenger/reservations")
async def read_passenger_reservations(
    current_user: Annotated[User, Depends(get_current_active_passenger)],
):
    return {"msg": f"Reservations for passenger {current_user.username}"}

# Endpoint accessible only by staff
@app.get("/staff/dashboard")
async def read_staff_dashboard(
    current_user: Annotated[User, Depends(get_current_active_staff)],
):
    return {"msg": f"Dashboard for staff {current_user.username}"}
