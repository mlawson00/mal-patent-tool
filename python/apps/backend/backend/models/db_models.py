import datetime
from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from pydantic import BaseModel
import os
print(os.listdir())
from backend.models.base import Base

class InternalUser(BaseModel):
	external_sub_id: str
	internal_sub_id: str
	username: str
	created_at: datetime.datetime

class postgresInternalUser(Base):
    __tablename__ = 'postgresInternalUser'

    email = Column(String, primary_key=True)
    username = Column(String)
    external_sub_id = Column(String)


    def __init__(self,
                 email,
                 username,
                 external_sub_id):

        self.email = email
        self.username = username
        self.external_sub_id = external_sub_id