window.onload = function () {
  $.ajax({
    url: "/spotify/listeningHistory.php",
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
    url: "/spotify/listeningHistory.php",
    method: "GET",
    success: function (data) {
      //"01", "02", "03", "04", "05", "06", 
      //0, 0, 0, 0, 0, 0, 
      var songs = ["07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"];
      var plays = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

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
            label: "Hourly Listen History",
            borderColor: "#3e95cd",
            fill: false
          }
          ]
        },
        options: {
          title: {
            display: true,
            text: 'Hourly Listens'
          }
        }

      });

      $("#orders_7").click(function () {
        var data = hourlyLineChart.data;
        data.labels = songs;
        data.datasets[0].data = plays;
        hourlyLineChart.update();
      });
    }
  })

  $.ajax({
    url: "/spotify/listeningHistory.php",
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
    url: "/spotify/songs.php",
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
            { "data": "playCount", "title": "Play Count" },
          ]
        });
      });
    }
  })
};