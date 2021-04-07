# Analytics for Spotify ![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/tests/badge.svg)![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/CodeQL/badge.svg)

### WIP


Self Hosted Last.FM Alternative to keeping track of your Spotify History


Current Features:
* Keeps Track of Listening History
* Keeps Track of how many times a song is played
* Includes Local Files*
* Ability to view un-playable songs in a Spotify Playlist

Notes:

* Will not include Private Sessions
* Offline Mode Not Supported (Currently)
* Ignores Scrubbing Through Songs (Counts as one Play)
* A play is counted after the 30 second mark
* If you play one song consecutively only the first play is counted (Currently)* 
* Requires Spotify Developer App to be Created

#### Internal Site / Local Network Use Only, <br>Not Designed to be Public / Internet Facing.
![Alt text](img/SpotifyAnalyticsSample.png?raw=true "Sample Output")
![Alt text](img/SonyPlayPlaylistDistribution.png?raw=true "Sample Output")



## Installation Instructions
## This contains only installation instructions. Thier are currently no Update Instructions!!!
### Instructions are for installing a VM / No Other Websites Hosted.
### This Project is a work in progress.<br> The database structure could change in future versions.
#### Installation Instructions are also a work in progress and were tested on Ubuntu Server 20.04.2.
I currently run this virtualized on a Virtual Machine running Debian 10.
#### Please Thoroughly Read The Instructions 
### Note:
This must run on a machine that is always on or<br />
it must be on and running when you want to keep track of play history.

Ideal Setup is a Local Server or a Local Machine<br />

Do not run on an external machine or allow external network access.<br />
It is Not Setup for Secure External Operation. 

Default Installation are as follows. <br />

### Get Spotify API Credentials:
Create a Non-Commercial Spotify App: https://developer.spotify.com/dashboard

For API Redirect URL Box<br />
Same Machine: http://localhost:PORT/analytics/loginResponse<br />
Local Server http://IPV4ADDRESS:PORT/analytics/loginResponse <br>
(Replace with the Local IPv4 Address of your server)<br />

#### For Django Test Server (Option 1) 
Use Port 8000 if you plan to test manually and not integrate it with Apache Web Server


#### For Apache (Option 2) (Recommended For Long Term)
Port 80 is recommended. However if you already using port 80 for another service, you will need to use a different port. 

#### Note:
Keep Track of your Client ID, Secret Key, and Redirect Url<br />

The port number doesn't matter as long your consistent.<br>
For Apache, for not using port 80, you will need to change the default port or make another virtual host.

### Source Code:
SSH into Local Server or run on local machine.<br />
Default Installation is ~/.

```
cd ~/
git clone https://github.com/ArthurVardevanyan/Analytics-for-Spotify.git
```


### Local Database Setup:
If you have a mariaDB or mySQL database setup with proper credentials, you may skip this section.
```
sudo apt-get install mariadb-server
```
Log Into MySql (sudo password, if asked)
```
sudo mysql
```
Within mysql Create User, Grant Privileges, and create database. <br/> 
Note: Alter statement may error out on older versions of MySql, you can ignore the error and continue.
```
CREATE USER 'spotify'@'localhost' IDENTIFIED BY 'spotify'; 
GRANT ALL PRIVILEGES ON *.* TO 'spotify'@'localhost';
alter user 'spotify'@'localhost' identified with mysql_native_password by 'spotify';
flush privileges;
create database spotify;
exit;
```

The default database credentials are:
```
host = localhost
database = spotify
user = spotify
password = spotify
```
### Project Setup :
Run the setup.py to setup the project.
```
sudo apt-get install python3-pip libmariadb-dev
```
```
cd Analytics-for-Spotify
pip3 install -r requirements.txt
python3 setup.py
```
The setup will ask for Spotify API Credentials and Database Credentials. 

### Option 1: Django Test Server Command Line
```
python3 manage.py runserver --noreload
```
After Navigating to the IP:PORT, Click "Start Service" (Django Default is port 8000)

### Option 2: WSGI Apache WebServer Setup (Recommended For Long Term):
If you have an existing webserver you will need to modify the below to run on a different port / virtual host.<br>
Otherwise just delete everything in the file below and replace with this.<br>
You must change "PATH_TO_PROGRAM" with your path. 
```
sudo pip3 install -r requirements.txt
sudo apt-get install apache2 libapache2-mod-wsgi-py3
sudo nano /etc/apache2/sites-available/000-default.conf 
```

```
<VirtualHost *:80>
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        Alias /spotify  /PATH_TO_PROGRAM/Analytics-for-Spotify/webFrontend
        <Directory /PATH_TO_PROGRAM/Analytics-for-Spotify/webFrontend>
            Require all granted
        </Directory>

        <Directory /PATH_TO_PROGRAM/Analytics-for-Spotify/AnalyticsforSpotify>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>

        WSGIDaemonProcess AnalyticsforSpotify python-path=//PATH_TO_PROGRAM/Analytics-for-Spotify/
        WSGIScriptAlias / /PATH_TO_PROGRAM/Analytics-for-Spotify/AnalyticsforSpotify/wsgi.py process-group=AnalyticsforSpotify application-group=%{GLOBAL}
        WSGIProcessGroup AnalyticsforSpotify
</VirtualHost>
```

```
sudo systemctl restart apache2
```
After Navigating to the IP:PORT, Click "Start Service"


### Final Notes

For either option, the server needs to be running to keep track of songs.


To update the API if you want to change the IP and/or PORT for the Redirect URIs. <br>

Make a backup of the database first.<br>

Click "Stop Service" in the Web API, and wait for the Service to Stop. (Manually Refresh The Page)<br>

Then Run setup.py again.<br><br>
