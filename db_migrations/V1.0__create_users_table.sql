CREATE TABLE IF NOT EXISTS users
(
    id      int NOT NULL,
    chat_id int NOT NULL,
    PRIMARY KEY (chat_id)
);

INSERT INTO users (id, chat_id) VALUES (0, 0);
