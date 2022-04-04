from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

engine = create_engine(f"postgres://{os.environ['PG_USER']}:{os.environ['PG_PASS']}@{os.environ['PG_URL']}/{os.environ['PG_DB']}")
Base = declarative_base()
#Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)