SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

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
) ;

-- --------------------------------------------------------

--
-- Table structure for table `listeningHistory`
--

CREATE TABLE `listeningHistory` (
  `timestamp` bigint NOT NULL,
  `timePlayed` text NOT NULL,
  `songID` varchar(22) NOT NULL,
  `json` json DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `songArtists`
--

CREATE TABLE `songArtists` (
  `songID` varchar(22) ,
  `artistID` varchar(22) 
) ;

-- --------------------------------------------------------

--
-- Table structure for table `songs`
--

CREATE TABLE `songs` (
  `id` varchar(22) ,
  `name` text NOT NULL,
  `playCount` int DEFAULT '1',
  `trackLength` bigint NOT NULL
) ;

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
