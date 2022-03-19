CREATE TABLE IF NOT EXISTS api_keys
(
    chat_id int          NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    PRIMARY KEY (api_key),
    CONSTRAINT fk_users FOREIGN KEY (chat_id) REFERENCES users (chat_id)
);

INSERT INTO api_keys (chat_id, api_key)
VALUES (0, '0');
