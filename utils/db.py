from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Using SQLite for metadata as a local replacement if PostgreSQL isn't pre-configured
# but structure is compatible with PostgreSQL
SQLALCHEMY_DATABASE_URL = "sqlite:///./metadata.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # 'admin', 'radiologist', 'researcher'

class PatientStudy(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True, index=True)
    patient_uuid = Column(String, index=True) # Anonymized ID
    study_date = Column(DateTime, default=datetime.datetime.utcnow)
    file_path = Column(String) # Encrypted file storage path
    metadata_json = Column(LargeBinary) # Fernet encrypted metadata

def init_db():
    Base.metadata.create_all(bind=engine)