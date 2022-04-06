import datetime
from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from pydantic import BaseModel
import os
print(os.listdir())
from backend.models.base import Base

class InternalUser(BaseModel):
	internal_sub_id: str
	external_sub_id: str
	username: str
	created_at: datetime.datetime

class postgresInternalUser(Base):
    __tablename__ = 'postgresInternalUser'

    internal_sub_id = Column(String, primary_key=True)
    external_sub_id = Column(String)
    username = Column(String)
    created_at = Column(TIMESTAMP)


    def __init__(self,
                 internal_sub_id,
                 external_sub_id,
                 username,
                 created_at):

        self.external_sub_id = internal_sub_id
        self.internal_sub_id = external_sub_id
        self.username = username
        self.created_at = created_at
