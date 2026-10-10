-- ====================================================================
-- Database Schema for Real-Time Object Detection & Logging Platform
-- Assignment 5 - Community Engagement Program
-- ====================================================================

-- 1. Create the database if it does not already exist
CREATE DATABASE IF NOT EXISTS `vision_platform`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `vision_platform`;

-- 2. Create the detection_logs table
CREATE TABLE IF NOT EXISTS `detection_logs` (
    `log_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for each logged detection event',
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp when detection was recorded',
    `object_class` VARCHAR(100) NOT NULL COMMENT 'Name/label of detected object (e.g. person, cell phone)',
    `confidence` FLOAT NOT NULL COMMENT 'Detection confidence score (0.0 to 1.0)',
    `bbox_x` INT NOT NULL COMMENT 'Bounding box top-left X coordinate',
    `bbox_y` INT NOT NULL COMMENT 'Bounding box top-left Y coordinate',
    `bbox_w` INT NOT NULL COMMENT 'Bounding box width in pixels',
    `bbox_h` INT NOT NULL COMMENT 'Bounding box height in pixels',
    INDEX `idx_timestamp` (`timestamp`),
    INDEX `idx_object_class` (`object_class`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sample query to verify table functionality:
-- SELECT * FROM detection_logs ORDER BY timestamp DESC LIMIT 10;
