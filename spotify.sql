-- phpMyAdmin SQL Dump
-- version 4.9.2deb1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Mar 21, 2020 at 09:47 AM
-- Server version: 8.0.19-0ubuntu4
-- PHP Version: 7.4.3

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `spotify`
--

-- --------------------------------------------------------

--
-- Table structure for table `artists`
--

CREATE TABLE `artists` (
  `id` varchar(22) NOT NULL,
  `name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `listeningHistory`
--

CREATE TABLE `listeningHistory` (
  `timestamp` bigint NOT NULL,
  `timePlayed` text NOT NULL,
  `songID` varchar(22) NOT NULL,
  `json` json DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `songArtists`
--

CREATE TABLE `songArtists` (
  `songID` varchar(22) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `artistID` varchar(22) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `songs`
--

CREATE TABLE `songs` (
  `id` varchar(22) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `name` text NOT NULL,
  `playCount` int DEFAULT '1',
  `trackLength` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `artists`
--
ALTER TABLE `artists`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `listeningHistory`
--
ALTER TABLE `listeningHistory`
  ADD PRIMARY KEY (`timestamp`),
  ADD KEY `songID` (`songID`);

--
-- Indexes for table `songArtists`
--
ALTER TABLE `songArtists`
  ADD KEY `id` (`songID`),
  ADD KEY `artistId` (`artistID`);

--
-- Indexes for table `songs`
--
ALTER TABLE `songs`
  ADD PRIMARY KEY (`id`);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `listeningHistory`
--
ALTER TABLE `listeningHistory`
  ADD CONSTRAINT `listeningHistory_ibfk_1` FOREIGN KEY (`songID`) REFERENCES `songs` (`id`) ON UPDATE CASCADE;

--
-- Constraints for table `songArtists`
--
ALTER TABLE `songArtists`
  ADD CONSTRAINT `songArtists_ibfk_1` FOREIGN KEY (`songID`) REFERENCES `songs` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `songArtists_ibfk_2` FOREIGN KEY (`artistID`) REFERENCES `artists` (`id`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
