import databases
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


def create_engine():
    # Create the database
    engine = sqlalchemy.create_engine(str(database.url))
    metadata.create_all(engine)
