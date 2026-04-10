CREATE TABLE IF NOT EXISTS upcoming_events
(
    id varchar(255) NOT NULL PRIMARY KEY,
    name varchar(255),
    date date NOT NULL,
    location varchar(255),
    link varchar(255) NOT NULL
);
