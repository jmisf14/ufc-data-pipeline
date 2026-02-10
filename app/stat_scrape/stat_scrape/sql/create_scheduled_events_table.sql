CREATE TABLE IF NOT EXISTS scheduled_events
(
    id varchar(255) PRIMARY KEY,
    name varchar(255),
    date date,
    location varchar(255),
    link varchar(255) NOT NULL
);

