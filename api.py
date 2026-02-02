from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Body
from contextlib import asynccontextmanager
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from utils.security import EncryptionHandler, log_audit_event, verify_password, create_access_token, get_password_hash
from utils.db import SessionLocal, User, PatientStudy
from solver import run_diagnostic_pipeline
from jose import JWTError, jwt
import threading, time, os

SECRET_KEY = os.environ.get("HIPAA_SECRET_KEY", "7b6f634f6d3957545366436e59325453")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    db = SessionLocal()
    if not db.query(User).filter(User.username == "radiologist_user").first():
        new_user = User(
            username="radiologist_user",
            hashed_password=get_password_hash("secure_pass123"),
            role="radiologist"
        )
        db.add(new_user)
        db.commit()
    db.close()
    yield
    # Shutdown logic (optional)

app = FastAPI(title="HIPAA Medical Imaging API", lifespan=lifespan)

def shutdown_timer(): 
    time.sleep(600)
    os._exit(0)
threading.Thread(target=shutdown_timer, daemon=True).start()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        return {"username": username, "role": role}
    except JWTError:
        raise credentials_exception

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        log_audit_event("unknown", "login_attempt", "none", "failed")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    log_audit_event(user.username, "login", "none", "success")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/diagnose")
async def diagnose_image(
    current_user: dict = Depends(get_current_user),
    history: str = Body(...),
    file: UploadFile = File(...)
):
    if current_user["role"] not in ["radiologist", "admin"]:
        log_audit_event(current_user["username"], "unauthorized_access", "diagnose", "denied")
        raise HTTPException(status_code=403, detail="Not authorized to perform diagnosis")
    
    # Save dummy file to root for simulation
    temp_path = f"/root/MedicalReportAnalysis/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
        
    results = run_diagnostic_pipeline(temp_path, history)
    log_audit_event(current_user["username"], "run_pipeline", file.filename, "success")
    
    return results

@app.get("/health")
def health_check():
    return {"status": "compliant", "api": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        ssl_keyfile="key.pem", 
        ssl_certfile="cert.pem"
    )

