-- MySQL compatible schema update script

-- Drop existing tables if they exist to start fresh, or modify as needed.
-- We'll provide a clean creation script for the new structure.

DROP TABLE IF EXISTS `predictions`;
DROP TABLE IF EXISTS `features`;
DROP TABLE IF EXISTS `temperature`;
DROP TABLE IF EXISTS `precipitation`;
DROP TABLE IF EXISTS `malaria_cases`;
DROP TABLE IF EXISTS `dengue_cases`;
DROP TABLE IF EXISTS `locations`;
DROP TABLE IF EXISTS `gadm_locations`;

CREATE TABLE `locations` (
    `location_id` INT NOT NULL AUTO_INCREMENT,
    `country` VARCHAR(100) DEFAULT NULL,
    `state_code` VARCHAR(10) DEFAULT NULL,
    `state_name` VARCHAR(100) DEFAULT NULL,
    `municipality` VARCHAR(150) DEFAULT NULL,
    `ibge_code` VARCHAR(20) DEFAULT NULL,
    `latitude` DECIMAL(10,8) DEFAULT NULL,
    `longitude` DECIMAL(11,8) DEFAULT NULL,
    `geometry` LONGTEXT,
    PRIMARY KEY (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `dengue_cases` (
    `dengue_id` INT NOT NULL AUTO_INCREMENT,
    `location_id` INT DEFAULT NULL,
    `report_date` DATE DEFAULT NULL,
    `year` INT DEFAULT NULL,
    `month` INT DEFAULT NULL,
    `week` INT DEFAULT NULL,
    `cases` INT DEFAULT NULL,
    `source` VARCHAR(150) DEFAULT NULL,
    `source_url` TEXT,
    PRIMARY KEY (`dengue_id`),
    KEY `location_id` (`location_id`),
    CONSTRAINT `fk_dengue_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `malaria_cases` (
    `malaria_id` INT NOT NULL AUTO_INCREMENT,
    `location_id` INT DEFAULT NULL,
    `notification_date` DATE DEFAULT NULL,
    `year` INT DEFAULT NULL,
    `month` INT DEFAULT NULL,
    `week` INT DEFAULT NULL,
    `cases` INT DEFAULT NULL,
    `laboratory_result` VARCHAR(50) DEFAULT NULL,
    `source` VARCHAR(150) DEFAULT NULL,
    `source_url` TEXT,
    PRIMARY KEY (`malaria_id`),
    KEY `location_id` (`location_id`),
    CONSTRAINT `fk_malaria_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `precipitation` (
    `precipitation_id` INT NOT NULL AUTO_INCREMENT,
    `location_id` INT DEFAULT NULL,
    `observation_date` DATE DEFAULT NULL,
    `year` INT DEFAULT NULL,
    `month` INT DEFAULT NULL,
    `week` INT DEFAULT NULL,
    `rainfall_mm` DECIMAL(8,2) DEFAULT NULL,
    `source` VARCHAR(150) DEFAULT NULL,
    PRIMARY KEY (`precipitation_id`),
    KEY `location_id` (`location_id`),
    CONSTRAINT `fk_precip_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `temperature` (
    `temperature_id` INT NOT NULL AUTO_INCREMENT,
    `location_id` INT DEFAULT NULL,
    `observation_date` DATE DEFAULT NULL,
    `year` INT DEFAULT NULL,
    `month` INT DEFAULT NULL,
    `week` INT DEFAULT NULL,
    `temperature_c` DECIMAL(5,2) DEFAULT NULL,
    `source` VARCHAR(150) DEFAULT NULL,
    PRIMARY KEY (`temperature_id`),
    KEY `location_id` (`location_id`),
    CONSTRAINT `fk_temp_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `features` (
    `feature_id` INT NOT NULL AUTO_INCREMENT,
    `location_id` INT DEFAULT NULL,
    `date` DATE DEFAULT NULL,
    `dengue_lag_1` INT DEFAULT NULL,
    `dengue_lag_2` INT DEFAULT NULL,
    `dengue_lag_4` INT DEFAULT NULL,
    `dengue_rolling_4` INT DEFAULT NULL,
    `malaria_lag_1` INT DEFAULT NULL,
    `malaria_lag_4` INT DEFAULT NULL,
    `rainfall_1` DECIMAL(8,2) DEFAULT NULL,
    `rainfall_2` DECIMAL(8,2) DEFAULT NULL,
    `rainfall_4` DECIMAL(8,2) DEFAULT NULL,
    `rainfall_8` DECIMAL(8,2) DEFAULT NULL,
    `temperature_1` DECIMAL(5,2) DEFAULT NULL,
    `temperature_2` DECIMAL(5,2) DEFAULT NULL,
    `temperature_4` DECIMAL(5,2) DEFAULT NULL,
    `rainfall_anomaly` DECIMAL(8,2) DEFAULT NULL,
    `temperature_anomaly` DECIMAL(5,2) DEFAULT NULL,
    `outbreak_target` TINYINT(1) DEFAULT NULL,
    PRIMARY KEY (`feature_id`),
    KEY `location_id` (`location_id`),
    CONSTRAINT `fk_features_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `predictions` (
    `prediction_id` INT NOT NULL AUTO_INCREMENT,
    `location_id` INT DEFAULT NULL,
    `prediction_date` DATE DEFAULT NULL,
    `target_date` DATE DEFAULT NULL,
    `disease` VARCHAR(50) DEFAULT NULL,
    `risk_probability` DECIMAL(5,4) DEFAULT NULL,
    `risk_level` VARCHAR(20) DEFAULT NULL,
    `model_version` VARCHAR(50) DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`prediction_id`),
    KEY `location_id` (`location_id`),
    CONSTRAINT `fk_predictions_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
