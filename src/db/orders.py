from dataclasses import dataclass

from sqlalchemy import BigInteger, Column, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OrderModel(Base):

    __tablename__ = "orders"

    api_key = Column(String)
    symbol = Column(String)
    orderId = Column(Integer, primary_key=True)
    orderListId = Column(Integer)
    clientOrderId = Column(String)
    price = Column(Float)
    origQty = Column(Float)
    executedQty = Column(Float)
    cummulativeQuoteQty = Column(Float)
    status = Column(String)
    timeInForce = Column(String)
    type = Column(String)
    side = Column(String)
    stopPrice = Column(Float)
    icebergQty = Column(Float)
    time = Column(BigInteger)
    updateTime = Column(BigInteger)
    isWorking = Column(Integer)
    origQuoteOrderQty = Column(Float)
    base_coin = Column(String)
    quote_coin = Column(String)
    name = Column(String(30))


@dataclass
class OrderEntry:
    api_key: str
    symbol: str
    orderIdr: int
    orderListIdr: int
    clientOrderId: str
    price: float
    origQty: float
    executedQty: float
    cummulativeQuoteQty: float
    status: str
    timeInForce: str
    type: str
    side: str
    stopPrice: float
    icebergQty: float
    time: int
    updateTime: int
    isWorking: int
    origQuoteOrderQty: float
    base_coin: str
    quote_coin: str
    name: str


class OrderDAO:
    def __init__(self, session):
        self._session = session
