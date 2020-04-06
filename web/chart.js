window.onload = function () {
  $.ajax({
    url: "http://localhost:8000/analytics/listeningHistory/",
    method: "GET",
    success: function (data) {
      var songs = [];
      var plays = [];

      for (var i in data) {
        day = data[i].timePlayed.slice(0, 10);
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
    url: "http://localhost:8000/analytics/listeningHistory/",
    method: "GET",
    success: function (data) {
      //"01", "02", "03", "04", "05", "06", 
      //0, 0, 0, 0, 0, 0, 
      var songs = ["06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"];
      var plays = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

      for (var i in data) {
        hour = data[i].timePlayed.slice(11, 13);
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
        //var last = new Date(date.getTime() - (days * 24 * 60 * 60 * 1000));
        var newDay = (date.getFullYear() + '-' + ('0' + (date.getMonth() + 1)).slice(-2) + '-' + ('0' + date.getDate()).slice(-2));

        var dailySongs = ["06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"];
        var dailyPlays = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

        for (var i in data) {
          day = data[i].timePlayed.slice(0, 10);
          hour = data[i].timePlayed.slice(11, 13);
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
    url: "http://localhost:8000/analytics/listeningHistory/",
    method: "GET",
    success: function (data) {
      $(document).ready(function () {
        //https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables
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
    url: "http://127.0.0.1:8000/analytics/songs",
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
    url: "http://127.0.0.1:8000/analytics/playlistSongs/",
    method: "GET",
    success: function (data) {
      $(document).ready(function () {
        //https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables
        var aDemoItems = data;
        if (data.length > 0) {
          document.getElementById("playlistHeader").innerHTML = "Playlist Songs"
          document.getElementById("playlists").innerHTML = "Last Updated: " + data[0]["lastUpdated"]

          //Load  data table
          var oTblReport = $("#playlist")

          oTblReport.DataTable({
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
      });
    }
  })
  $.ajax({
    url: "http://localhost:8000/analytics/listeningHistory/",
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