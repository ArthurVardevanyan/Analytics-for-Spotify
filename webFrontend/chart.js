function deleteCookies() {
  const allCookies = document.cookie.split(";");
  // https://www.geeksforgeeks.org/how-to-clear-all-cookies-using-javascript/
  // The "expire" attribute of every cookie is
  // Set to "Thu, 01 Jan 1970 00:00:00 GMT"
  for (let i = 0; i < allCookies.length; i++) {
    document.cookie = `${allCookies[i]}=;expires=${new Date(0).toUTCString()}`;
  }
  $.post("/analytics/logout/", function () {
    window.location.href = "/spotify/index.html";
  });
}

function start() {
  $.post("/analytics/start/", function () {
    window.location.href = "/spotify/analytics.html";
  });
}
function stop() {
  $.post("/analytics/stop/", function () {
    window.location.href = "/spotify/analytics.html";
  });
}

function deleteUser() {
  $.post("/analytics/delete/", function () {
    window.location.href = "/spotify/index.html";
  });
}

function playlist() {
  $.post(
    "/analytics/playlistSubmission/",
    { playlist: document.getElementById("playlist").value },
    function () {
      window.location.href = "/spotify/analytics.html";
    }
  );
}

function deletePlaylist(id) {
  $.post("/analytics/deletePlaylist/", { playlist: id });
  window.location.href = "/spotify/analytics.html";
}

window.onload = function () {
  $.ajax({
    url: "/analytics/authenticated/",
    method: "GET",
    success(data) {
      if (data === "False") {
        window.location.href = "/spotify/index.html";
      }
    },
  });

  $.ajax({
    url: "/analytics/status/",
    method: "GET",
    success(data) {
      data = data.split(":");
      if (data[0] === "1") {
        document.getElementById("status").innerHTML =
          "<h3 style='margin: 0px; color:green'>Service is Running</h3>";
      } else if (data[1] === "1") {
        document.getElementById("status").innerHTML =
          "<h3 style='margin: 0px; color:yellow'>Service is being Stopped</h3>";
      } else if (data[1] === "0") {
        document.getElementById("status").innerHTML =
          "<h3 style='margin: 0px; color:red'>Service is not Running</h3>";
      }
      if (data[2] === "0") {
        document.getElementById("realTime").style.display = "";
        document.getElementById("realTime").innerHTML =
          "<h3 style='margin: 0px; color:black'>Their may be up to a 20 minute delay in song history.</h3>";
      }
    },
  });

  topSongs();

  $.ajax({
    url: "/analytics/listeningHistory/",
    method: "GET",
    success(data) {
      playlistSongs();
      stats(data);
      summaryLineChart(data);
      hourlyLineChart(data);
      listeningHistory(data);
    },
  });
};
function topSongs() {
  $.ajax({
    url: "/analytics/songs",
    method: "GET",
    success(data) {
      $(document).ready(() => {
        // https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables
        const aDemoItems = data;

        // Load  data table
        const oTblReport = $("#songs");

        oTblReport.DataTable({
          data: aDemoItems,
          order: [[2, "desc"]],
          pageLength: 10,
          columns: [
            { data: "name", title: "Song Name" },
            { data: "artists", title: "Artists" },
            { data: "playCount", title: "Count" },
          ],
        });
      });
    },
  });
}
function playlistSongs() {
  $.ajax({
    url: "/analytics/playlistSongs/",
    method: "GET",
    success(data) {
      $(document).ready(() => {
        // https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables
        for (let i = 0; i < data.length; i++) {
          var aDemoItems = data[i].tracks;

          if (aDemoItems.length > 0) {
            var time = data[i].lastUpdated.split(" ");
            lt = new Date(time[0] + "T" + time[1] + "+00:00");
            localDateTime = `${lt.getFullYear()}-${`0${
              lt.getMonth() + 1
            }`.slice(-2)}-${`0${lt.getDate()}`.slice(
              -2
            )} ${`0${lt.getHours()}`.slice(-2)}:${`0${lt.getMinutes()}`.slice(
              -2
            )}:${`0${lt.getSeconds()}`.slice(-2)}`;

            tableName = data[i].name.replace(/ /g, "_");
            document.getElementById(
              "playlists"
            ).innerHTML += `<div class="playlistDIV"><br><h2>Playlist: ${data[i].name} </h2> <h3>Last Updated: ${localDateTime}</h3> <button onclick=deletePlaylist("${data[i].id}") style="color: black" class="btn">Delete</button><table id="playlist_${i}" class="display" width="100%"></table>
              <div class="songSpread"><canvas id="songSpread_${data[i].id}" width="800" height="450"></canvas></div></div>`;
          }
        }
        for (let i = 0; i < data.length; i++) {
          var aDemoItems = data[i].tracks;

          if (aDemoItems.length > 0) {
            // Load  data table
            $(`#playlist_${i}`).DataTable({
              data: aDemoItems,
              order: [[3, "desc"]],
              pageLength: 10,
              columns: [
                { data: "name", title: "Song Name" },
                { data: "artists", title: "Artists" },
                { data: "timePlayed", title: "LastPlayed" },
                { data: "songStatus", title: "Status" },
                { data: "playCount", title: "Count" },
              ],
            });
          }
        }

        for (let i = 0; i < data.length; i++) {
          var aDemoItems = data[i].tracks;

          if (aDemoItems.length > 0) {
            const songs = [];
            const plays = [];

            for (const i in aDemoItems) {
              if (aDemoItems[i].timePlayed != null) {
                localTime = new Date(
                  aDemoItems[i].timePlayed + "T" + "00:00:00" + "+00:00"
                );
              } else {
                localTime = new Date(aDemoItems[i].timePlayed);
              }
              day = `${localTime.getFullYear()}-${`0${
                localTime.getMonth() + 1
              }`.slice(-2)}-${`0${localTime.getDate()}`.slice(-2)}`;
              if (songs.includes(day)) {
                for (let j = 0; j < songs.length; j++) {
                  if (day === songs[j]) {
                    plays[j] = plays[j] + 1;
                  }
                }
              } else {
                songs.push(day);
                plays.push(1);
              }
            }
            const weekSongs = [];
            const weekPlays = [];
            let count = 0;
            let temp = 0;
            for (let index = 0; index < songs.length; index++) {
              if (count === 7) {
                weekSongs.push(songs[index - 7]);
                weekPlays.push(temp);
                temp = 0;
                count = 0;
              }
              temp += plays[index];
              count += 1;
            }
            if (count !== 0) {
              weekSongs.push(songs[songs.length - count]);
              weekPlays.push(temp);
              temp = 0;
              count = 0;
            }
            id = `songSpread_${data[i].id}`;
            const barChart = new Chart(document.getElementById(id), {
              type: "bar",
              data: {
                labels: weekSongs,
                datasets: [
                  {
                    data: weekPlays,
                    label: "Amount of Songs By The Week",
                    backgroundColor: "#3e95cd",
                    fill: false,
                  },
                ],
              },
              options: {
                title: {
                  display: true,
                  text: "When Songs Where Last Played",
                },
                scales: {
                  yAxes: [
                    {
                      ticks: {
                        beginAtZero: true,
                      },
                    },
                  ],
                },
              },
            });
            barChart.update();
          }
        }
      });
    },
  });
}

function summaryLineChart(data) {
  const songs = [];
  const plays = [];

  for (const i in data) {
    var time = data[i].timePlayed.split(" ");
    localTime = new Date(time[0] + "T" + time[1] + "+00:00");
    day = `${localTime.getFullYear()}-${`0${localTime.getMonth() + 1}`.slice(
      -2
    )}-${`0${localTime.getDate()}`.slice(-2)}`;
    if (songs.includes(day)) {
      for (let j = 0; j < songs.length; j++) {
        if (day === songs[j]) {
          plays[j] = plays[j] + 1;
        }
      }
    } else {
      songs.push(day);
      plays.push(1);
    }
  }
  const lineChart = new Chart(document.getElementById("line-chart"), {
    type: "line",
    data: {
      labels: songs,
      datasets: [
        {
          data: plays,
          label: "Listen History",
          borderColor: "#3e95cd",
          fill: false,
        },
      ],
    },
    options: {
      title: {
        display: true,
        text: "Listens Per Day",
      },
      scales: {
        yAxes: [
          {
            ticks: {
              beginAtZero: true,
            },
          },
        ],
      },
    },
  });
  $("#orders_1").click(() => {
    const { data } = lineChart;
    const yearSongs = [];
    const yearPlays = [];

    const days = 365; // Days you want to subtract
    const date = new Date();
    const last = new Date(date.getTime() - days * 24 * 60 * 60 * 1000);
    const newDay = `${last.getFullYear()}-${`0${last.getMonth() + 1}`.slice(
      -2
    )}-${`0${last.getDate()}`.slice(-2)}`;

    for (let index = 0; index < songs.length; index++) {
      if (newDay < songs[index]) {
        yearSongs.push(songs[index]);
        yearPlays.push(plays[index]);
      }
    }

    const weekSongs = [];
    const weekPlays = [];
    let count = 0;
    let temp = 0;
    for (let index = 0; index < songs.length; index++) {
      if (count === 7) {
        weekSongs.push(songs[index - 7]);
        weekPlays.push(temp);
        temp = 0;
        count = 0;
      }
      temp += plays[index];
      count += 1;
    }
    if (count !== 0) {
      weekSongs.push(songs[songs.length - count]);
      weekPlays.push(temp);
      temp = 0;
      count = 0;
    }
    data.labels = weekSongs;
    data.datasets[0].data = weekPlays;

    lineChart.update();
  });
  $("#orders_2").click(() => {
    const { data } = lineChart;
    const yearSongs = [];
    const yearPlays = [];

    const days = 30; // Days you want to subtract
    const date = new Date();
    const last = new Date(date.getTime() - days * 24 * 60 * 60 * 1000);
    const newDay = `${last.getFullYear()}-${`0${last.getMonth() + 1}`.slice(
      -2
    )}-${`0${last.getDate()}`.slice(-2)}`;

    for (let index = 0; index < songs.length; index++) {
      if (newDay < songs[index]) {
        yearSongs.push(songs[index]);
        yearPlays.push(plays[index]);
      }
    }

    data.labels = yearSongs;
    data.datasets[0].data = yearPlays;

    lineChart.update();
  });
  $("#orders_3").click(() => {
    const { data } = lineChart;
    const yearSongs = [];
    const yearPlays = [];

    const days = 7; // Days you want to subtract
    const date = new Date();
    const last = new Date(date.getTime() - days * 24 * 60 * 60 * 1000);
    const newDay = `${last.getFullYear()}-${`0${last.getMonth() + 1}`.slice(
      -2
    )}-${`0${last.getDate()}`.slice(-2)}`;

    for (let index = 0; index < songs.length; index++) {
      if (newDay < songs[index]) {
        yearSongs.push(songs[index]);
        yearPlays.push(plays[index]);
      }
    }

    data.labels = yearSongs;
    data.datasets[0].data = yearPlays;

    lineChart.update();
  });
  document.getElementById("orders_2").click();
}

function hourlyLineChart(data) {
  const songs = [
    "00",
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
  ];
  const plays = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  ];
  for (const i in data) {
    var time = data[i].timePlayed.split(" ");
    localTime = new Date(time[0] + "T" + time[1] + "+00:00");
    hour = `0${String(localTime.getHours())}`.slice(-2);
    // hour = data[i].timePlayed.slice(11, 13);
    for (let j = 0; j < songs.length; j++) {
      if (hour === songs[j]) {
        plays[j] = plays[j] + 1;
      }
    }
  }
  const hourlyLineChart = new Chart(
    document.getElementById("hourlyLine-chart"),
    {
      type: "line",
      data: {
        labels: songs,
        datasets: [
          {
            data: plays,
            label: "Average Hourly Listen History",
            borderColor: "#3e95cd",
            fill: false,
          },
        ],
      },
      options: {
        title: {
          display: true,
          text: "Average Hourly Listens",
        },
      },
    }
  );

  $("#orders_8").click(() => {
    const chartData = hourlyLineChart.data;
    chartData.labels = songs;
    chartData.datasets[0].data = plays;
    hourlyLineChart.update();
  });
  $("#orders_4").click(() => {
    const chartData = hourlyLineChart.data;
    const date = new Date(document.getElementById("datePicker").value);
    const newDay = `${date.getFullYear()}-${`0${date.getMonth() + 1}`.slice(
      -2
    )}-${`0${date.getDate()}`.slice(-2)}`;

    const dailySongs = [
      "00",
      "01",
      "02",
      "03",
      "04",
      "05",
      "06",
      "07",
      "08",
      "09",
      "10",
      "11",
      "12",
      "13",
      "14",
      "15",
      "16",
      "17",
      "18",
      "19",
      "20",
      "21",
      "22",
      "23",
    ];
    const dailyPlays = [
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    ];

    for (const i in data) {
      localTime = new Date(`${data[i].timePlayed}`);
      day = `${localTime.getFullYear()}-${`0${localTime.getMonth() + 1}`.slice(
        -2
      )}-${`0${localTime.getDate()}`.slice(-2)}`;
      hour = `0${String(localTime.getHours())}`.slice(-2);

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
function listeningHistory(data) {
  $(document).ready(() => {
    // https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables

    for (let i = 0; i < data.length; i++) {
      var time = data[i].timePlayed.split(" ");
      lt = new Date(time[0] + "T" + time[1] + "+00:00");
      localDateTime = `${lt.getFullYear()}-${`0${lt.getMonth() + 1}`.slice(
        -2
      )}-${`0${lt.getDate()}`.slice(-2)} ${`0${lt.getHours()}`.slice(
        -2
      )}:${`0${lt.getMinutes()}`.slice(-2)}:${`0${lt.getSeconds()}`.slice(-2)}`;
      data[i].timePlayed = localDateTime;
    }

    const aDemoItems = data;

    // Load  data table
    if ($.fn.DataTable.isDataTable("#listeningHistory")) {
      $("#listeningHistory").DataTable().destroy();
    }
    const oTblReport = $("#listeningHistory");
    oTblReport.DataTable({
      data: aDemoItems,
      order: [[0, "desc"]],
      pageLength: 10,
      columns: [
        { data: "timePlayed", title: "Time Played", width: "135" },
        { data: "name", title: "Song Name" },
      ],
    });
  });
}
function stats(data) {
  timeListened = 0;
  SongsListenedTo = data.length;
  for (const i in data) {
    timeListened = timeListened += parseInt(data[i].trackLength);
  }
  timeListened = Math.round((timeListened / 60000 / 60) * 10) / 10;
  document.getElementById(
    "statsDesktop"
  ).innerHTML = `Songs Listened To: ${SongsListenedTo} & Hours Listened To: ${timeListened}`;
  document.getElementById(
    "statsMobile"
  ).innerHTML = `Songs Listened To: ${SongsListenedTo}<br>Hours Listened To: ${timeListened}`;
}
