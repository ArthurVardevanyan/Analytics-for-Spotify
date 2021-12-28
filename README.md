# Analytics for Spotify

**Production:** ![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/tests/badge.svg?branch=production)![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/CodeQL/badge.svg?branch=production) [![Coverage Status](https://coveralls.io/repos/github/ArthurVardevanyan/Analytics-for-Spotify/badge.svg?branch=production)](https://coveralls.io/github/ArthurVardevanyan/Analytics-for-Spotify?branch=production)

**Develop:** ![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/tests/badge.svg?branch=develop)![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/CodeQL/badge.svg?branch=develop) [![Coverage Status](https://coveralls.io/repos/github/ArthurVardevanyan/Analytics-for-Spotify/badge.svg?branch=develop)](https://coveralls.io/github/ArthurVardevanyan/Analytics-for-Spotify?branch=develop)

## Work In Progress

Self Hosted Last.FM Alternative to keeping track of your Spotify History

Current Features:

- Keeps Track of Listening History
- Keeps Track of how many times a song is played
- Includes Local Files*
- Ability to view un-playable songs in a Spotify Playlist

Notes:

- Will not include Private Sessions
- Offline Mode Not Supported (Currently)
- Ignores Scrubbing Through Songs (Counts as one Play)
- A play is counted after the 30 second mark
- If you play one song consecutively only the first play is counted (Currently)*
- Requires Spotify Developer App to be Created

### Internal Site / Local Network Use Only

Not Designed to be Public / Internet Facing.

## Spotify API

### Scopes

These are the scopes used by the application.

- [User Read Currently Playing](https://developer.spotify.com/documentation/general/guides/authorization/scopes/#user-read-currently-playing)
- [User Read Recently Played](https://developer.spotify.com/documentation/general/guides/authorization/scopes/#user-read-recently-played)

### Endpoints

These are the endpoints used by the application.

- [Get Current User's Profile](https://developer.spotify.com/documentation/web-api/reference/#/operations/get-current-users-profile)
- [Get Recently Played Tracks](https://developer.spotify.com/documentation/web-api/reference/#/operations/get-recently-played)
- [Get Playlist](https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlist)
- [Get Currently Playing Track](https://developer.spotify.com/documentation/web-api/reference/#/operations/get-the-users-currently-playing-track)

## Sample Images

![Analytics For Spotify Sample](img/AnalyticsForSpotifySample.png?raw=true "Sample Output") ![Song Play Playlist Distribution](img/SongPlayPlaylistDistribution.png?raw=true "Sample Output")
