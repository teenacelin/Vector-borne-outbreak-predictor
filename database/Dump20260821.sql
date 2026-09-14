-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: vector_predictor
-- ------------------------------------------------------
-- Server version	5.7.40-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `dengue_cases`
--

DROP TABLE IF EXISTS `dengue_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dengue_cases` (
  `dengue_id` int(11) NOT NULL AUTO_INCREMENT,
  `location_id` int(11) DEFAULT NULL,
  `report_date` date DEFAULT NULL,
  `year` int(11) DEFAULT NULL,
  `month` int(11) DEFAULT NULL,
  `cases` int(11) DEFAULT NULL,
  PRIMARY KEY (`dengue_id`),
  KEY `location_id` (`location_id`),
  CONSTRAINT `dengue_cases_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `gadm_locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dengue_cases`
--

LOCK TABLES `dengue_cases` WRITE;
/*!40000 ALTER TABLE `dengue_cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `dengue_cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gadm_locations`
--

DROP TABLE IF EXISTS `gadm_locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gadm_locations` (
  `location_id` int(11) NOT NULL AUTO_INCREMENT,
  `country` varchar(100) DEFAULT NULL,
  `state_code` varchar(10) DEFAULT NULL,
  `state_name` varchar(100) DEFAULT NULL,
  `municipality` varchar(150) DEFAULT NULL,
  `geometry` longtext,
  PRIMARY KEY (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gadm_locations`
--

LOCK TABLES `gadm_locations` WRITE;
/*!40000 ALTER TABLE `gadm_locations` DISABLE KEYS */;
/*!40000 ALTER TABLE `gadm_locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `malaria_cases`
--

DROP TABLE IF EXISTS `malaria_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `malaria_cases` (
  `malaria_id` int(11) NOT NULL AUTO_INCREMENT,
  `location_id` int(11) DEFAULT NULL,
  `notification_date` date DEFAULT NULL,
  `year` int(11) DEFAULT NULL,
  `month` int(11) DEFAULT NULL,
  `laboratory_result` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`malaria_id`),
  KEY `location_id` (`location_id`),
  CONSTRAINT `malaria_cases_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `gadm_locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `malaria_cases`
--

LOCK TABLES `malaria_cases` WRITE;
/*!40000 ALTER TABLE `malaria_cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `malaria_cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `precipitation`
--

DROP TABLE IF EXISTS `precipitation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `precipitation` (
  `precipitation_id` int(11) NOT NULL AUTO_INCREMENT,
  `location_id` int(11) DEFAULT NULL,
  `observation_date` date DEFAULT NULL,
  `year` int(11) DEFAULT NULL,
  `month` int(11) DEFAULT NULL,
  `rainfall_mm` decimal(8,2) DEFAULT NULL,
  PRIMARY KEY (`precipitation_id`),
  KEY `location_id` (`location_id`),
  CONSTRAINT `precipitation_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `gadm_locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `precipitation`
--

LOCK TABLES `precipitation` WRITE;
/*!40000 ALTER TABLE `precipitation` DISABLE KEYS */;
/*!40000 ALTER TABLE `precipitation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `temperature`
--

DROP TABLE IF EXISTS `temperature`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `temperature` (
  `temperature_id` int(11) NOT NULL AUTO_INCREMENT,
  `location_id` int(11) DEFAULT NULL,
  `observation_date` date DEFAULT NULL,
  `year` int(11) DEFAULT NULL,
  `month` int(11) DEFAULT NULL,
  `temperature_c` decimal(5,2) DEFAULT NULL,
  PRIMARY KEY (`temperature_id`),
  KEY `location_id` (`location_id`),
  CONSTRAINT `temperature_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `gadm_locations` (`location_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `temperature`
--

LOCK TABLES `temperature` WRITE;
/*!40000 ALTER TABLE `temperature` DISABLE KEYS */;
/*!40000 ALTER TABLE `temperature` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-21  8:30:29
