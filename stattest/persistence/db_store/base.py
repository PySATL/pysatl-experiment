from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

SessionType = scoped_session[Session]


class ModelBase(DeclarativeBase):
    pass
