<?php
//https://www.dyclassroom.com/chartjs/chartjs-how-to-draw-bar-graph-using-data-from-mysql-table-and-php
//setting header to json
header('Content-Type: application/json');

//database
include 'credentials.php';

//query to get data from the table
$query = sprintf('SELECT playlists.lastUpdated, playlistSongs.songStatus, songs.name as "name", `playCount`, GROUP_CONCAT(artists.name  SEPARATOR", ") as "artists" FROM playlistSongs
INNER JOIN songs ON songs.id =playlistSongs.songID 
INNER JOIN songArtists ON songs.id=songArtists.songID
INNER JOIN artists ON artists.id=songArtists.artistID
INNER JOIN playlists ON playlists.id=playlistSongs.playlistID
GROUP BY songs.id  
');

//execute query
$result = $mysqli->query($query);

//loop through the returned data
$data = array();
foreach ($result as $row) {
  $data[] = $row;
}

//free memory associated with result
$result->close();

//close connection
$mysqli->close();

//now print the data
print json_encode($data);
