from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

engine = create_engine(f"postgresql://{os.environ['PG_USER']}:{os.environ['PG_PASS']}@{os.environ['PG_URL']}/{os.environ['PG_DB']}")

# engine = create_engine('postgresql://usr:pass@postgres:5432/sqlalchemy')

Base = declarative_base()
#Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)