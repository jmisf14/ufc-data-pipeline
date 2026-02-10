CREATE TABLE IF NOT EXISTS scheduled_fights
(
    id varchar(255) PRIMARY KEY,
    event_id varchar(255) NOT NULL,
    red_id varchar(255) NOT NULL,
    blue_id varchar(255) NOT NULL,
    division varchar(255),
    link varchar(255) NOT NULL
);

