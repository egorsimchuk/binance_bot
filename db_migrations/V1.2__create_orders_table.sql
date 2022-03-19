CREATE TABLE IF NOT EXISTS orders
(
    api_key             VARCHAR(255) NOT NULL,
    symbol              VARCHAR(255),
    orderId             int,
    orderListId         int,
    clientOrderId       VARCHAR(255),
    price               double precision,
    origQty             double precision,
    executedQty         double precision,
    cummulativeQuoteQty double precision,
    status              VARCHAR(255),
    timeInForce         VARCHAR(255),
    type                VARCHAR(255),
    side                VARCHAR(255),
    stopPrice           double precision,
    icebergQty          double precision,
    time                bigint,
    updateTime          bigint,
    isWorking           int,
    origQuoteOrderQty   double precision,
    base_coin           VARCHAR(255),
    quote_coin          VARCHAR(255),
    PRIMARY KEY (orderId),
    CONSTRAINT fk_api_keys FOREIGN KEY (api_key) REFERENCES api_keys (api_key)
);

INSERT INTO orders
VALUES ('0', 'SOLUSDT', 325002460, -1, 'ios_ab3cb1da3asdfuafdgsdkj2345b', 10.0, 1, 1, 1, 'FILLED', 'GTC',
        'LIMIT', 'BUY', 0.0, 0.0, 1621031032220, 1621061234380, 1, 0.0, 'SOL', 'USDT');