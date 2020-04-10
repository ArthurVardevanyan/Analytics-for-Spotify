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
  `user` varchar(30) NOT NULL,
  `timestamp` bigint NOT NULL,
  `timePlayed` text NOT NULL,
  `songID` varchar(22) NOT NULL,
  `json` json DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `playcount`
--

CREATE TABLE `playcount` (
  `user` varchar(30) NOT NULL,
  `song` varchar(22) NOT NULL,
  `playCount` int NOT NULL DEFAULT '1'
) ;

-- --------------------------------------------------------

--
-- Table structure for table `playlists`
--

CREATE TABLE `playlists` (
  `user` varchar(30) NOT NULL,
  `id` varchar(100) NOT NULL,
  `name` text NOT NULL,
  `lastUpdated` text NOT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `playlistSongs`
--

CREATE TABLE `playlistSongs` (
  `playlistID` varchar(100) NOT NULL,
  `songID` varchar(22) NOT NULL,
  `songStatus` text NOT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `songArtists`
--

CREATE TABLE `songArtists` (
  `songID` varchar(22) NOT NULL,
  `artistID` varchar(22) NOT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `songs`
--

CREATE TABLE `songs` (
  `id` varchar(22) NOT NULL,
  `name` text NOT NULL,
  `trackLength` bigint NOT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user` varchar(30) NOT NULL
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
  ADD PRIMARY KEY (`timestamp`,`user`) USING BTREE,
  ADD KEY `songID` (`songID`),
  ADD KEY `user` (`user`);

--
-- Indexes for table `playcount`
--
ALTER TABLE `playcount`
  ADD PRIMARY KEY (`user`,`song`),
  ADD KEY `song` (`song`);

--
-- Indexes for table `playlists`
--
ALTER TABLE `playlists`
  ADD PRIMARY KEY (`id`,`user`) USING BTREE,
  ADD KEY `user` (`user`);

--
-- Indexes for table `playlistSongs`
--
ALTER TABLE `playlistSongs`
  ADD UNIQUE KEY `songID` (`songID`),
  ADD KEY `playlistID` (`playlistID`);

--
-- Indexes for table `songArtists`
--
ALTER TABLE `songArtists`
  ADD PRIMARY KEY (`songID`,`artistID`),
  ADD KEY `id` (`songID`),
  ADD KEY `artistId` (`artistID`);

--
-- Indexes for table `songs`
--
ALTER TABLE `songs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user`);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `listeningHistory`
--
ALTER TABLE `listeningHistory`
  ADD CONSTRAINT `listeningHistory_ibfk_1` FOREIGN KEY (`songID`) REFERENCES `songs` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `listeningHistory_ibfk_2` FOREIGN KEY (`user`) REFERENCES `users` (`user`);

--
-- Constraints for table `playcount`
--
ALTER TABLE `playcount`
  ADD CONSTRAINT `playcount_ibfk_1` FOREIGN KEY (`user`) REFERENCES `users` (`user`),
  ADD CONSTRAINT `playcount_ibfk_2` FOREIGN KEY (`song`) REFERENCES `songs` (`id`);

--
-- Constraints for table `playlists`
--
ALTER TABLE `playlists`
  ADD CONSTRAINT `playlists_ibfk_1` FOREIGN KEY (`user`) REFERENCES `users` (`user`);

--
-- Constraints for table `playlistSongs`
--
ALTER TABLE `playlistSongs`
  ADD CONSTRAINT `playlistSongs_ibfk_1` FOREIGN KEY (`playlistID`) REFERENCES `playlists` (`id`),
  ADD CONSTRAINT `playlistSongs_ibfk_2` FOREIGN KEY (`songID`) REFERENCES `songs` (`id`);

--
-- Constraints for table `songArtists`
--
ALTER TABLE `songArtists`
  ADD CONSTRAINT `songArtists_ibfk_1` FOREIGN KEY (`songID`) REFERENCES `songs` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `songArtists_ibfk_2` FOREIGN KEY (`artistID`) REFERENCES `artists` (`id`) ON UPDATE CASCADE;
COMMIT;
