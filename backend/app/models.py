from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False, unique=True)
    private_key = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    preshared_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
