DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS words CASCADE;
DROP TABLE IF EXISTS user_words CASCADE;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS words (
    id SERIAL PRIMARY KEY,
    word VARCHAR UNIQUE,
    translation VARCHAR
);

CREATE TABLE IF NOT EXISTS user_words (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    word VARCHAR,
    translation VARCHAR,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO words (word, translation) VALUES
('red', 'красный'),
('blue', 'синий'),
('green', 'зелёный'),
('yellow', 'жёлтый'),
('black', 'чёрный'),
('white', 'белый'),
('I', 'я'),
('you', 'ты'),
('he', 'он'),
('she', 'она')
ON CONFLICT (word) DO NOTHING;
