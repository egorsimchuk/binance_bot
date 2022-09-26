import os
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOSTNAME = os.environ.get("DB_HOSTNAME", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_NAME = os.environ.get("DB_NAME", "postgres")


class SessionWrapper:
    def __init__(self, session: Session):
        self._session = session

    def __enter__(self):
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        # make sure the dbconnection gets closed
        if exc_type is not None:
            self._session.rollback()
        self._session.close()


class SessionFactory:
    def __init__(self, engine):
        self._sessionmaker = sessionmaker(bind=engine)

    def __call__(self):
        return SessionWrapper(self._sessionmaker())


def create_session_factory():
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"
    )
    return SessionFactory(engine)


from src.db.orders import OrderEntry


class OrderDAO:
    def __init__(self, session):
        self._session = session

    def create(self, order_entry: OrderEntry):
        """Create signal"""
        with self._session() as session:
            from src.db.orders import OrderModel

            order = OrderModel()
            session.add(order)
            session.commit()


if __name__ == "__main__":
    session_factory = create_session_factory()
    new_entry = OrderEntry(
        (
            "0",
            "SOLUSDT",
            325002460,
            -1,
            "ios_ab3cb1da3asdfuafdgsdkj2345b",
            10.0,
            1,
            1,
            1,
            "FILLED",
            "GTC",
            "LIMIT",
            "BUY",
            0.0,
            0.0,
            1621031032220,
            1621061234380,
            1,
            0.0,
            "SOL",
            "USDT",
        )
    )
    print()
