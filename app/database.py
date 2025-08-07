from decimal import Decimal
from datetime import datetime, timedelta
from flask import (
    current_app
)
from sqlalchemy import (
    create_engine,
    inspect,
    Integer,
    Column,
    String,
    DateTime,
    Date,
    ForeignKey,
    Numeric,
    Boolean,
)
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    Session,
    relationship,
)
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

#from app.utils import get_time
#session = None
#db_insp = None


#session = Session(engine, future=True)

Base = declarative_base()
engine = create_engine('postgresql+psycopg2://postgres:example@postgres:5432/biota')
session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))
db_insp = inspect(engine)

Base.query = session.query_property()
