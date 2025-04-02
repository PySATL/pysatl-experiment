import sqlite3
from abc import ABC
from typing import ClassVar

import numpy as np
from sqlalchemy.orm import scoped_session, sessionmaker
from typing_extensions import override

from stattest.persistence.db_store.base import ModelBase, SessionType
from stattest.persistence.db_store.db_init import get_request_or_thread_id, init_db
from stattest.persistence.models import IStore


class AbstractDbStore(IStore, ABC):
    session: ClassVar[SessionType]

    def __init__(self, db_url="sqlite:///pysatl.sqlite"):
        super().__init__()
        self.db_url = db_url

    @override
    def init(self):
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        engine = init_db(self.db_url)
        AbstractDbStore.session = scoped_session(
            sessionmaker(bind=engine, autoflush=False), scopefunc=get_request_or_thread_id
        )
        ModelBase.metadata.create_all(engine)
