from sqlalchemy import Column, String, Integer, Boolean, ForeignKey,TIMESTAMP
from sqlalchemy.orm import relationship, backref

from base import Base


class DB_users(Base):

    __tablename__ = 'db_users'

    internal_sub_id = Column('internal_sub_id', String, primary_key=True)
    external_sub_id = Column('external_sub_id', String)
    username = Column('username', String)
    created_at = Column('created_at', TIMESTAMP)

    def __init__(self, internal_sub_id, external_sub_id, username, created_at):
        self.internal_sub_id = internal_sub_id
        self.external_sub_id = external_sub_id
        self.username = username
        self.created_at = created_at