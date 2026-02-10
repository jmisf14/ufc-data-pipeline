INSERT INTO fighter_images (fighter_id, image_url)
VALUES (
    %s,
    %s
)
ON CONFLICT (fighter_id) DO UPDATE
SET image_url = EXCLUDED.image_url;

