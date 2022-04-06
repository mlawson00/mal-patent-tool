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
instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]

db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
engine = sqlalchemy.create_engine(

    # Equivalent URL:
    # postgresql+pg8000://<db_user>:<db_pass>@/<db_name>
    #                         ?unix_sock=<socket_path>/<cloud_sql_instance_name>/.s.PGSQL.5432
    # Note: Some drivers require the `unix_sock` query parameter to use a different key.
    # For example, 'psycopg2' uses the path set to `host` in order to connect successfully.
    sqlalchemy.engine.url.URL.create(
        drivername="postgresql+pg8000",
        username=db_user,  # e.g. "my-database-user"
        password=db_pass,  # e.g. "my-database-password"
        database=db_name,  # e.g. "my-database-name"
        query={
            "host": "{}/{}/.s.PGSQL.5432".format(
                db_socket_dir,  # e.g. "/cloudsql"
                instance_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
        }
    )
)



# engine = create_engine(f"postgresql://{os.environ['PG_USER']}:{os.environ['PG_PASS']}@{os.environ['PG_URL']}/{os.environ['PG_DB']}")

#engine = create_engine('postgresql://usr:pass@0.0.0.0:5432/sqlalchemy')

Base = declarative_base()
#Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)