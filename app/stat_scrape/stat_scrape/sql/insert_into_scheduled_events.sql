INSERT INTO scheduled_events (id, name, date, location, link)
VALUES (
    %s,
    %s,
    %s,
    %s,
    %s
)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    date = EXCLUDED.date,
    location = EXCLUDED.location,
    link = EXCLUDED.link;

