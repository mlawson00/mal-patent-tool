import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Remember - storing secrets in plaintext is potentially unsafe. Consider using
# something like https://cloud.google.com/secret-manager/docs/overview to help keep
# secrets secret.
db_user = os.environ["DB_USER"]
db_pass = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]

if "INSTANCE_CONNECTION_NAME" in os.environ:

    instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]
    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    engine = sqlalchemy.create_engine(

        sqlalchemy.engine.url.URL.create(
            drivername="postgresql",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            database=db_name,  # e.g. "my-database-name"
            query={
                "host": "{}/{}".format(
                    db_socket_dir,  # e.g. "/cloudsql"
                    instance_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
            }#
        )
    )
else:
    print('starting from here')
    print(f'postgresql://{db_user}:{db_pass}@cloudsqlproxy:3305/{db_name}')
    engine = sqlalchemy.create_engine(f'postgresql://{db_user}:{db_pass}@cloudsqlproxy:3305/{db_name}')

Base = declarative_base()
#Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)