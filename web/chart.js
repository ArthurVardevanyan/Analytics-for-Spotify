function deleteCookies() {
  var allCookies = document.cookie.split(';');
  //https://www.geeksforgeeks.org/how-to-clear-all-cookies-using-javascript/
  // The "expire" attribute of every cookie is  
  // Set to "Thu, 01 Jan 1970 00:00:00 GMT" 
  for (var i = 0; i < allCookies.length; i++) {
    document.cookie = allCookies[i] + "=;expires="
      + new Date(0).toUTCString();
  }
}

function playlist() {
  window.location.href = "/analytics/playlistSubmission?playlist=" + document.getElementById("playlist").value
}


function deletePlaylist(id) {
  window.location.href = "/analytics/deletePlaylist?playlist=" + id
}

window.onload = function () {

  $.ajax({
    url: "/analytics/authenticated/",
    method: "GET",
    success: function (data) {
      if (data === "False") {
        window.location.href = "/spotify";
      }
    }

  });

  $.ajax({
    url: "/analytics/status/",
    method: "GET",
    success: function (data) {
      data = data.split(':')
      if (data[0] === "1") { document.getElementById("status").innerHTML = "<h3 style='margin: 0px; color:green'>Service is Running</h3>"; }
      else {
        if (data[1] === "1") {
          document.getElementById("status").innerHTML = "<h3 style='margin: 0px; color:yellow'>Service is being Stopped</h3>";
        } else if (data[1] === "0") {
          document.getElementById("status").innerHTML = "<h3 style='margin: 0px; color:red'>Service is not Running</h3>";
        }
      }

    }
  });
  $.ajax({
    url: "/analytics/listeningHistory/",
    method: "GET",
    success: function (data) {
      var songs = [];
      var plays = [];

      for (var i in data) {
        localTime = new Date(data[i].timePlayed + ' UTC');
        day = (localTime.getFullYear() + '-' + ('0' + (localTime.getMonth() + 1)).slice(-2) + '-' + ('0' + localTime.getDate()).slice(-2));
        if (songs.includes(day)) {
          for (let j = 0; j < songs.length; j++) {
            if (day === songs[j]) {
              plays[j] = plays[j] + 1;
            }
          }
        }
        else {
          songs.push(day);
          plays.push(1);
        }

      }
      var lineChart = new Chart(document.getElementById("line-chart"), {
        type: 'line',
        data: {
          labels: songs,
          datasets: [{
            data: plays,
            label: "Listen History",
            borderColor: "#3e95cd",
            fill: false
          }
          ]
        },
        options: {
          title: {
            display: true,
            text: 'Listens Per Day'
          },
          scales: {
            yAxes: [{
              ticks: {
                beginAtZero: true
              }
            }]
          }
        }
      });
      $("#orders_1").click(function () {
        var data = lineChart.data;
        var yearSongs = [];
        var yearPlays = [];

        var days = 365; // Days you want to subtract
        var date = new Date();
        var last = new Date(date.getTime() - (days * 24 * 60 * 60 * 1000));
        var newDay = (last.getFullYear() + '-' + ('0' + (last.getMonth() + 1)).slice(-2) + '-' + ('0' + last.getDate()).slice(-2));

        for (let index = 0; index < songs.length; index++) {
          if (newDay < songs[index]) {
            yearSongs.push(songs[index])
            yearPlays.push(plays[index])
          }
        }

        data.labels = yearSongs;
        data.datasets[0].data = yearPlays;


        lineChart.update();
      });
      $("#orders_2").click(function () {
        var data = lineChart.data;
        var yearSongs = [];
        var yearPlays = [];

        var days = 30; // Days you want to subtract
        var date = new Date();
        var last = new Date(date.getTime() - (days * 24 * 60 * 60 * 1000));
        var newDay = (last.getFullYear() + '-' + ('0' + (last.getMonth() + 1)).slice(-2) + '-' + ('0' + last.getDate()).slice(-2));

        for (let index = 0; index < songs.length; index++) {
          if (newDay < songs[index]) {
            yearSongs.push(songs[index])
            yearPlays.push(plays[index])
          }
        }

        data.labels = yearSongs;
        data.datasets[0].data = yearPlays;


        lineChart.update();
      });
      $("#orders_3").click(function () {
        var data = lineChart.data;
        var yearSongs = [];
        var yearPlays = [];

        var days = 7; // Days you want to subtract
        var date = new Date();
        var last = new Date(date.getTime() - (days * 24 * 60 * 60 * 1000));
        var newDay = (last.getFullYear() + '-' + ('0' + (last.getMonth() + 1)).slice(-2) + '-' + ('0' + last.getDate()).slice(-2));

        for (let index = 0; index < songs.length; index++) {
          if (newDay < songs[index]) {
            yearSongs.push(songs[index])
            yearPlays.push(plays[index])
          }
        }

        data.labels = yearSongs;
        data.datasets[0].data = yearPlays;


        lineChart.update();
      });
    }
  });
  $.ajax({
    url: "/analytics/listeningHistory/",
    method: "GET",
    success: function (data) {


      var songs = [
        "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11",
        "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"];
      var plays = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
      for (var i in data) {
        localTime = new Date(data[i].timePlayed + ' UTC');
        hour = ('0' + String(localTime.getHours())).slice(-2);
        //hour = data[i].timePlayed.slice(11, 13);
        for (let j = 0; j < songs.length; j++) {
          if (hour === songs[j]) {
            plays[j] = plays[j] + 1;
          }
        }


      }
      var hourlyLineChart = new Chart(document.getElementById("hourlyLine-chart"), {
        type: 'line',
        data: {
          labels: songs,
          datasets: [{
            data: plays,
            label: "Average Hourly Listen History",
            borderColor: "#3e95cd",
            fill: false
          }
          ]
        },
        options: {
          title: {
            display: true,
            text: 'Average Hourly Listens'
          }
        }

      });

      $("#orders_8").click(function () {
        var chartData = hourlyLineChart.data;
        chartData.labels = songs;
        chartData.datasets[0].data = plays;
        hourlyLineChart.update();
      });
      $("#orders_4").click(function () {
        var chartData = hourlyLineChart.data;
        var date = new Date(document.getElementById("datePicker").value);
        var newDay = (date.getFullYear() + '-' + ('0' + (date.getMonth() + 1)).slice(-2) + '-' + ('0' + date.getDate()).slice(-2));

        var dailySongs = [
          "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11",
          "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"];
        var dailyPlays = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

        for (var i in data) {
          localTime = new Date(data[i].timePlayed + ' UTC');
          day = (localTime.getFullYear() + '-' + ('0' + (localTime.getMonth() + 1)).slice(-2) + '-' + ('0' + localTime.getDate()).slice(-2));
          hour = ('0' + String(localTime.getHours())).slice(-2);

          for (let j = 0; j < dailySongs.length; j++) {
            if (day === newDay) {
              if (hour === dailySongs[j]) {
                dailyPlays[j] = dailyPlays[j] + 1;
              }
            }
          }

        }




        chartData.labels = dailySongs;
        chartData.datasets[0].data = dailyPlays;
        hourlyLineChart.update();
      });
    }
  })

  $.ajax({
    url: "/analytics/listeningHistory/",
    method: "GET",
    success: function (data) {
      $(document).ready(function () {
        //https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables

        for (let i = 0; i < data.length; i++) {
          lt = new Date(data[i].timePlayed + ' UTC');
          localDateTime = (lt.getFullYear() + '-' +
            ('0' + (lt.getMonth() + 1)).slice(-2) + '-' +
            ('0' + lt.getDate()).slice(-2) + " " +
            ('0' + lt.getHours()).slice(-2) + ":" +
            ('0' + lt.getMinutes()).slice(-2) + ":" +
            ('0' + lt.getSeconds()).slice(-2));
          data[i].timePlayed = localDateTime;
        }


        var aDemoItems = data;

        //Load  data table
        var oTblReport = $("#listeningHistory")

        oTblReport.DataTable({
          data: aDemoItems,
          "order": [[0, "desc"]],
          "pageLength": 10,
          "columns": [
            { "data": "timePlayed", "title": "Time Played", "width": "135" },
            { "data": "name", "title": "Song Name" },
          ]
        });
      });
    }
  })
  $.ajax({
    url: "/analytics/songs",
    method: "GET",
    success: function (data) {
      $(document).ready(function () {
        //https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables
        var aDemoItems = data;

        //Load  data table
        var oTblReport = $("#songs")

        oTblReport.DataTable({
          data: aDemoItems,
          "order": [[2, "desc"]],
          "pageLength": 10,
          "columns": [
            { "data": "name", "title": "Song Name" },
            { "data": "artists", "title": "Artists" },
            { "data": "playCount", "title": "Count" },
          ]
        });
      });
    }
  })
  $.ajax({
    url: "/analytics/playlistSongs/",
    method: "GET",
    success: function (data) {
      $(document).ready(function () {
        //https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables
        for (let i = 0; i < data.length; i++) {


          var aDemoItems = data[i]["tracks"];

          if (aDemoItems.length > 0) {

            lt = new Date(aDemoItems[0]["lastUpdated"] + ' UTC');
            localDateTime = (lt.getFullYear() + '-' +
              ('0' + (lt.getMonth() + 1)).slice(-2) + '-' +
              ('0' + lt.getDate()).slice(-2) + " " +
              ('0' + lt.getHours()).slice(-2) + ":" +
              ('0' + lt.getMinutes()).slice(-2) + ":" +
              ('0' + lt.getSeconds()).slice(-2));


            tableName = data[i]["name"].replace(/ /g, "_");
            document.getElementById("playlists").innerHTML +=
              '  <div class="playlistDIV"><br><h2>Playlist: ' + data[i]["name"] +
              ' </h2> <h3>Last Updated: '
              + localDateTime + '</h3> <button onclick=deletePlaylist("' + data[i]["hash"] + '") style="color: black" class="btn">Delete</button><table id="playlist_' + i + '" class="display" width="100%"></table></div>';
          }
        }
        for (let i = 0; i < data.length; i++) {
          var aDemoItems = data[i]["tracks"];

          if (aDemoItems.length > 0) {

            //Load  data table
            $('#playlist_' + i).DataTable({
              data: aDemoItems,
              "order": [[2, "desc"]],
              "pageLength": 10,
              "columns": [
                { "data": "name", "title": "Song Name" },
                { "data": "artists", "title": "Artists" },
                { "data": "songStatus", "title": "Status" },
                { "data": "playCount", "title": "Count" },
              ]
            });
          }
        }
      });
    }
  })
  $.ajax({
    url: "/analytics/listeningHistory/",
    method: "GET",
    success: function (data) {
      timeListened = 0;
      SongsListenedTo = data.length;
      for (var i in data) {
        timeListened = timeListened += parseInt(data[i].trackLength);
      }
      timeListened = Math.round(timeListened / 60000 / 60 * 10) / 10
      document.getElementById("statsDesktop").innerHTML = "Songs Listened To: " + SongsListenedTo + " & Hours Listened To: " + timeListened
      document.getElementById("statsMobile").innerHTML = "Songs Listened To: " + SongsListenedTo + "<br>Hours Listened To: " + timeListened
    }
  })

};