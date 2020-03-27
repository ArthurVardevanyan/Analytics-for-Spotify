<?php
define('DB_HOST', '127.0.0.1');
define('DB_USERNAME', 'spotify');
define('DB_PASSWORD', 'spotify');
define('DB_NAME', 'spotify');
//get connection
$mysqli = new mysqli(DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME);

if (!$mysqli) {
    die("Connection failed: " . $mysqli->error);
}
