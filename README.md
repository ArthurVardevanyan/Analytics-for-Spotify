# SpotifyAnalytics

Self Hosted Last.FM Alternative to keeping track of your Spotify History


Current Features:
* Keeps Track of Listening History
* Keeps Track of how many times a song is played
* Web Interface Yet, all data is stored in a DB
* Includes Local Files
* Ability to view un-playable songs in a Spotify Playlist: Currently Command Line Only 

Notes:

* Will not include Private Sessions
* Offline Mode Not Supported (Currently)
* Ignores Scrubbing Through Songs (Counts as one Play)
* A play is counted after the 30 second mark
* If you play one song consecutively only the first play is counted (Currently)
* Requires Spotify Developer App to be Created

![Alt text](img/SpotifyAnalyticsSample.png?raw=true "Sample Output")


## Installation Instructions
### This Project is a work in progress. The database structure could change in future versions.
#### Installation Instructions are also a work in progress and were tested on Ubuntu 18.04 LTS Server.
I currently run this virtualized on a Virtual Machine running Ubuntu 18.04 LTS Server.
#### Please Thoroughly Read The Instructions 
### Note:
This must run on a machine that is always on or<br />
it must be on and running when you want to keep track of play history.

Ideal Setup is a Local Server or a Local Machine<br />

Do not run on an external machine or allow external network access.<br />
It is Not Setup for Secure External Operation. 

Default Installation are as follows. <br />
If you would like to customize, please read through and make changes as you see fit.<br />

#### Nano Editor Shortcut Commands:
* Paste: Cntrl - Shift - V
* Save: Cntrl - O
* Exit: Cntrl - x


### Get Spotify Credentials:
Create a Non-Commercial Spotify App: https://developer.spotify.com/dashboard

For Redirect URL Box<br />
Same Machine: http://localhost:80<br />
Local Server http://IPV4ADDRESS:80 (Replace with the Local IPv4 Address of your server)<br />


Keep Track of your Client ID and Secret Key<br />
For Your Spotify Account ID https://www.spotify.com/is/account/profile/


### Code:
SSH into Local Server or run on local machine.<br />
Default Installation is ~/.

```
cd ~/
git clone https://github.com/ArthurVardevanyan/SpotifyAnalytics.git
```

### WebServer Setup:
If your webserver is already setup, you can skip this.
```
sudo apt-get install apache2 php libapache2-mod-php php-mysql
sudo systemctl restart apache2
```

### Database Setup:
```
sudo apt-get install mysql-server
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
alter user 'spotify'@'localhost' identified with mysql_native_password by 'spotify'
flush privileges;
create database spotify;
exit;
```
Load Tables into the spotify database. (Password is spotify)
```
sudo mysql -u spotify -p spotify < ~/SpotifyAnalytics/spotify.sql
```
#### Script Setup:
If you modified your database username and password, change them below for the webserver
```
nano ~/SpotifyAnalytics/web/credentials.php
```
Create a Link from webserver folder to script location
```
sudo ln -s  ~/SpotifyAnalytics/web/ /var/www/html/spotify
```
UnZip NodeModules
```
sudo apt-get install unzip
cd ~/SpotifyAnalytics/web
unzip *.zip
cd ~/SpotifyAnalytics/
```
If you modified your database username and password, change them below for the backend
```
nano   ~/SpotifyAnalytics/credentials/databaseCredentials.txt
```
Change as Needed<br />
Line 1: Username<br />
Line 2: Password<br />
Line 3: Database Name<br />

Enter Spotify Credentials <br />
Line 1: Client ID<br />
Line 2: Secret Key<br />
Line 3: Spotify Username<br />
```
nano   ~/SpotifyAnalytics/credentials/spotifyCredentials.txt
```
<br />

Change localhost to the local ip address of the server, must be same as entered in Spotify Web App<br />
(or keep localhost if your running on same system, this is only used for connecting the spotify account and nothing more afterwords)
```
nano ~/SpotifyAnalytics/authorization.py
```
Install python dependencies 
```
sudo apt-get install python3-pip
pip3 install  mysql-connector-python spotipy
```


### First Time Script Run

Run Via SSH or locally 
```
python3  ~/SpotifyAnalytics/spotify.py
```
Copy the URL into your Browser, (if running locally, browser may auto open)<br />
Copy the new URL after authorizing back into the Script (Hit Enter if doesn't auto advance)<br />

Two Successful Outputs Depending on whether your listening to music or not<br />
1. No Song Playing<br />
2. Song is Displayed and Counted<br />

Cntrl-C  Twice to exit

You can either run the script manually and leave it open to collect data or have it auto run on boot.

### To Auto Run Script On Boot
modify USER  to your username

```
nano  ~/SpotifyAnalytics/spotify.sh
```
Open crontab via nano 
```
sudo crontab -e
```
add below to the end of the file.<br />
Change USER to your Username

```
@reboot sh /home/USER/SpotifyAnalytics/spotify.sh &
```
Change USER to your Username
```
sudo chmod +x /home/USER/SpotifyAnalytics/spotify.sh
sudo reboot
```

Accessible via 
```
IP/spotify/
```