CREATE DATABASE IF NOT EXISTS ravid_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON ravid_db.* TO 'ravid_user'@'%';
FLUSH PRIVILEGES;

SELECT 'RAVID Database initialized successfully!' AS status; 