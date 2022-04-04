from pydantic import BaseModel
from backend.models.base import Base
from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, TIMESTAMP

class InternalAuthToken(BaseModel):
	code: str


class ExternalAuthToken(BaseModel):
	code: str


class InternalAccessTokenData(BaseModel):
	sub: str


class ExternalUser(BaseModel):
	email: str
	username: str
	external_sub_id: str

class postgresExternalUser(Base):
    __tablename__ = 'postgresExternalUser'

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

