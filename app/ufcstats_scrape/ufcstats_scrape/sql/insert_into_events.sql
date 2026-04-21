INSERT INTO events
VALUES (
    %s,
    %s,
    %s,
    %s,
    %s
)
ON CONFLICT DO NOTHING