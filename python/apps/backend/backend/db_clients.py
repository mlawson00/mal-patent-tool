from abc import ABC, abstractmethod
import datetime
import hashlib
import logging
from typing import List
from sqlalchemy import select
from uuid import uuid4

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
)
from passlib.hash import bcrypt
from pymongo.errors import ServerSelectionTimeoutError

from backend import config
from backend.exceptions import (
    DatabaseConnectionError,
    UnknownDatabaseType,
)
from backend.models.db_models import (
    InternalUser, postgresInternalUser
)
from backend.models.auth_models import (
    ExternalUser, postgresExternalUser
)

from backend.models.base import (
    engine, Session, Base
)

logger = logging.getLogger(__name__)


# doesn't seem to get used
def get_db_client(db_type):
    """ Works out the correct database client based on
		the database type provided in the configuration

		Raises:
			backend.exceptions.UnknownDatabaseType
	"""
    for client_cls in DatabaseClient.__subclasses__():
        try:
            if client_cls.meets_condition(db_type):
                return client_cls()
        except KeyError:
            continue

    raise UnknownDatabaseType(db_type)


class DatabaseClient(ABC):
    """ Database client interface """

    @abstractmethod
    def meets_condition(db_type: str):
        """ Checks whether this type of database client matches
			the one defined in the configuration.

			Makes sure the correct client will be instantiated.

			Args:
				db_type: One of database types as defined in config
		"""
        ...

    @abstractmethod
    async def close_connection(self):
        """ Closes a connection to the database """
        ...

    @abstractmethod
    async def start_session(self):
        """ Starts a session in the database.

			Usually called once at the start of the service.
			Stays open as long as the service is running.

			Raises:
				backend.exception.DatabaseConnectionError
		"""
        ...

    @abstractmethod
    async def end_session(self):
        """ Ends a session in the database. """
        ...

    @abstractmethod
    async def get_user_by_external_sub_id(self, external_user: ExternalUser) -> InternalUser:
        """ Returns a user from the database, based on the external sub_id of
			the current authentication provider (i.e Google, FaceBook etc)

			Args:
				external_user: An object representing a user with information
								based on the external provider's service.

			Returns:
				internal_user: A user objects as defined in this application
		"""
        ...

    @abstractmethod
    async def get_user_by_internal_sub_id(self, internal_sub_id: str) -> InternalUser:
        """ Returns a user from the database, based on the internal sub_id

			Args:
				internal_sub_id: The unique id of the user as defined in this application

			Returns:
				internal_user: A user objects as defined in this application
		"""
        ...

    @abstractmethod
    async def create_internal_user(self, external_user: ExternalUser) -> InternalUser:
        """ Creates a user in the database based on the external sub_id of
			the current authentication provider (i.e Google, FaceBook etc)

			The user will also be assigned an internal sub_id for authentication
			within the internal system (backend application)

			Args:
				external_user: An object representing a user with information
								based on the external provider's service.

			Returns:
				internal_user: A user objects as defined in this application
		"""
        ...

    @abstractmethod
    async def update_internal_user(self, internal_user: InternalUser) -> InternalUser:
        """ Updates a user in the database

			Args:
				internal_user: A user objects as defined in this application

			Returns:
				internal_user: A user objects as defined in this application
		"""
        ...

    async def _encrypt_external_sub_id(sefl, external_user: ExternalUser) -> str:
        """ It encrypts the subject id received from the external provider. These ids are
			used to uniquely identify a user in the system of the external provider and
			are usually public. However, it is better to be stored encrypted just in case.

			Args:
				external_user: An object representing a user with information
								based on the external provider's service.

			Returns:
				encrypted_external_sub_id: The encrypted external subject id
		"""
        salt = external_user.email.lower()
        salt = salt.replace(" ", "")
        # Hash the salt so that the email is not plain text visible in the database
        salt = hashlib.sha256(salt.encode()).hexdigest()
        # bcrypt requires a 22 char salt
        if len(salt) > 21:
            salt = salt[:21]

        # As per passlib the last character of the salt should always be one of [.Oeu]
        salt = salt + "O"

        encrypted_external_sub_id = bcrypt.using(salt=salt).hash(external_user.external_sub_id)
        return encrypted_external_sub_id


class PostgresDBClient(DatabaseClient):
    """ Wrapper around an AsyncIOMotorClient object. """

    def __init__(self):
        pass

    # TODO change this
    @staticmethod
    def meets_condition(db_type):
        return db_type == config.MONGO_DB

    # TODO change this
    async def close_connection(self):
        self._motor_client.close()

    #TODO change this
    async def start_session(self):
        try:
            self._session = await self._motor_client.start_session()
        except ServerSelectionTimeoutError as exc:
            raise DatabaseConnectionError(exc)

    # TODO change this
    async def end_session(self):
        await self._session.end_session()

    async def get_user_by_external_sub_id(self, external_user: ExternalUser) -> InternalUser:

        internal_user = None
        encrypted_external_sub_id = await self._encrypt_external_sub_id(external_user)

        session = Session()

        print(f'checking for postgres user by external sub_id: {encrypted_external_sub_id}')
        postgres_user = session.scalars(select(postgresInternalUser).where(
            postgresInternalUser.internal_sub_id == encrypted_external_sub_id)).first()
        print(f'this is what I found {postgres_user}')
        if postgres_user:
            print('found postgres user by external sub_id')
            internal_user = InternalUser(
                internal_sub_id=postgres_user.internal_sub_id,
                external_sub_id=postgres_user.external_sub_id,
                username=postgres_user.username,
                created_at=postgres_user.created_at
            )
        else:
            print('did not find postgres user by external sub_id')

        return internal_user

    async def get_user_by_internal_sub_id(self, internal_sub_id: str) -> InternalUser:
        internal_user = None

        session = Session()
        postgres_user = session.get(postgresInternalUser, internal_sub_id)
        if postgres_user is None:
            print(f'{internal_sub_id}: this is no postgres user')
        else:
            print(f'{internal_sub_id}: this is a postgres user, their ame is {postgres_user.username}')

        if postgres_user:
            internal_user = InternalUser(
                internal_sub_id=postgres_user.internal_sub_id,
                external_sub_id=postgres_user.external_sub_id,
                username=postgres_user.username,
                created_at=postgres_user.created_at
            )

        return internal_user

    async def create_internal_user(self, external_user: ExternalUser) -> InternalUser:
        encrypted_external_sub_id = await self._encrypt_external_sub_id(external_user)
        unique_identifier = str(uuid4())

        pg_int = postgresInternalUser(unique_identifier,
                                      encrypted_external_sub_id,
                                      external_user.username,
                                      datetime.datetime.utcnow())
        session = Session()
        session.add(pg_int)
        session.commit()
        session.close()

        postgres_user = session.get(postgresInternalUser, unique_identifier)

        internal_user = InternalUser(
            internal_sub_id=postgres_user.internal_sub_id,
            external_sub_id=postgres_user.external_sub_id,
            username=postgres_user.username,
            created_at=postgres_user.created_at,
        )
        return internal_user

    async def update_internal_user(self, internal_user: InternalUser) -> InternalUser:
        print('I am trying to update an internal user')
        updated_user = None

        result = await self._users_coll.update_one(
            {"internal_sub_id": internal_user.internal_sub_id},
            {"$set": internal_user.dict()}
        )

        if result.modified_count:
            updated_user = internal_user

        return updated_user
