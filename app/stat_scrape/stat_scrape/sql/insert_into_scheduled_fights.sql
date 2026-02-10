INSERT INTO scheduled_fights (id, event_id, red_id, blue_id, division, link)
VALUES (
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
)
ON CONFLICT (id) DO UPDATE
SET event_id = EXCLUDED.event_id,
    red_id = EXCLUDED.red_id,
    blue_id = EXCLUDED.blue_id,
    division = EXCLUDED.division,
    link = EXCLUDED.link;

