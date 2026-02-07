function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const CSRF_TOKEN = getCookie("csrftoken");

function deleteCookies() {
  const allCookies = document.cookie.split(";");
  // https://www.geeksforgeeks.org/how-to-clear-all-cookies-using-javascript/
  // The "expire" attribute of every cookie is
  // Set to "Thu, 01 Jan 1970 00:00:00 GMT"
  for (let i = 0; i < allCookies.length; i++) {
    document.cookie = `${allCookies[i]}=;expires=${new Date(0).toUTCString()}`;
  }
  $.ajax({
    url: "/analytics/logout/",
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    success() {
      window.location.href = "/spotify/index.html";
    },
  });
}

function start() {
  $.ajax({
    url: "/analytics/start/",
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    success() {
      window.location.href = "/spotify/analytics.html";
    },
  });
}

function stop() {
  $.ajax({
    url: "/analytics/stop/",
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    success() {
      window.location.href = "/spotify/analytics.html";
    },
  });
}

function deleteUser() {
  $.ajax({
    url: "/analytics/deleteUser/",
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    success() {
      window.location.href = "/spotify/index.html";
    },
  });
}

function playlist() {
  $.ajax({
    url: "/analytics/playlistSubmission/",
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    data: { playlist: document.getElementById("playlist").value },
    success() {
      window.location.href = "/spotify/analytics.html";
    },
  });
}

function deletePlaylist(id) {
  $.ajax({
    url: "/analytics/deletePlaylist/",
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    data: { playlist: id },
    success() {
      window.location.href = "/spotify/analytics.html";
    },
  });
}

window.onload = function () {
  $.ajax({
    url: "/analytics/authenticated/",
    method: "GET",
    success(data) {
      if (data !== "True") {
        window.location.href = "/spotify/index.html";
      }
    },
    error(data) {
      if (data !== "True") {
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
      if (data[2] === "0" || data[2] === "2") {
        document.getElementById("realTime").style.display = "";
        document.getElementById("realTime").innerHTML =
          "<h3 style='margin: 0px; color:black'>Their may be up to a 20 minute delay in song history.</h3>";
      }
    },
  });

  topSongs();

  $.ajax({
    url: "/analytics/stats/",
    method: "GET",
    success(data) {
      displayStats(data);
    },
  });

  $.ajax({
    url: "/analytics/dailyAggregation/",
    method: "GET",
    success(data) {
      summaryLineChart(data);
    },
  });

  $.ajax({
    url: "/analytics/hourlyAggregation/",
    method: "GET",
    success(data) {
      hourlyLineChart(data);
    },
  });

  listeningHistory();
};
function topSongs() {
  $.ajax({
    url: "/analytics/songs/",
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
            { data: "n", title: "Song Name" },
            { data: "a", title: "Artists" },
            { data: "pc", title: "Count" },
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
              -2,
            )} ${`0${lt.getHours()}`.slice(-2)}:${`0${lt.getMinutes()}`.slice(
              -2,
            )}:${`0${lt.getSeconds()}`.slice(-2)}`;

            tableName = data[i].name.replace(/ /g, "_");
            document.getElementById("playlists").innerHTML +=
              `<div class="playlistDIV"><br><h2>Playlist: ${data[i].name} </h2> <h3>Last Updated: ${localDateTime}</h3> <button onclick=deletePlaylist("${data[i].id}") style="color: black" class="btn">Delete</button><table id="playlist_${i}" class="display" width="100%"></table>
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
                { data: "n", title: "Song Name" },
                { data: "a", title: "Artists" },
                { data: "t", title: "LastPlayed" },
                { data: "ss", title: "Status" },
                { data: "pc", title: "Count" },
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
              if (aDemoItems[i].t != null) {
                localTime = new Date(
                  aDemoItems[i].t + "T" + "00:00:00" + "+00:00",
                );
              } else {
                localTime = new Date(aDemoItems[i].t);
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
                  y: {
                    beginAtZero: true,
                  },
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
  const songs = data.songs;
  const plays = data.plays;
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
          tension: 0.4,
        },
      ],
    },
    options: {
      title: {
        display: true,
        text: "Listens Per Day",
      },
      scales: {
        y: {
          beginAtZero: true,
        },
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
      -2,
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
      -2,
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
      -2,
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
  const songs = data.songs;
  const plays = data.plays;
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
            tension: 0.4,
          },
        ],
      },
      options: {
        title: {
          display: true,
          text: "Average Hourly Listens",
        },
      },
    },
  );

  $("#orders_8").click(() => {
    const chartData = hourlyLineChart.data;
    chartData.labels = songs;
    chartData.datasets[0].data = plays;
    hourlyLineChart.update();
  });
  $("#orders_4").click(() => {
    const chartData = hourlyLineChart.data;
    const selectedDate = document.getElementById("datePicker").value;

    if (!selectedDate) {
      alert("Please select a date first");
      return;
    }

    // Fetch hourly data for specific date from backend
    $.ajax({
      url: `/analytics/hourlyAggregation/?date=${selectedDate}`,
      method: "GET",
      success(dateData) {
        chartData.labels = dateData.songs;
        chartData.datasets[0].data = dateData.plays;
        hourlyLineChart.update();
      },
      error() {
        alert("Error loading date-specific data");
      },
    });
  });
}
function listeningHistory(loadAll = false) {
  const url = loadAll
    ? "/analytics/listeningHistory/"
    : "/analytics/listeningHistory/?limit=100";

  $.ajax({
    url: url,
    method: "GET",
    success(data) {
      $(document).ready(() => {
        // https://datatables.net/forums/discussion/32107/how-to-load-an-array-of-json-objects-to-datatables

        for (let i = 0; i < data.length; i++) {
          var time = data[i].t.split(" ");
          lt = new Date(time[0] + "T" + time[1] + "+00:00");
          localDateTime = `${lt.getFullYear()}-${`0${lt.getMonth() + 1}`.slice(
            -2,
          )}-${`0${lt.getDate()}`.slice(-2)} ${`0${lt.getHours()}`.slice(
            -2,
          )}:${`0${lt.getMinutes()}`.slice(-2)}:${`0${lt.getSeconds()}`.slice(
            -2,
          )}`;
          data[i].t = localDateTime;
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
            { data: "t", title: "Time Played", width: "170px" },
            { data: "n", title: "Song Name" },
          ],
        });

        // After initial load with 100 entries, load the rest in background along with playlists
        if (!loadAll && data.length === 100) {
          setTimeout(() => {
            listeningHistory(true);
            playlistSongs();
          }, 1000);
        }
      });
    },
  });
}
function displayStats(data) {
  const songsListenedTo = data.songsListenedTo;
  const hoursListened = data.hoursListened;
  document.getElementById("statsDesktop").innerHTML =
    `Songs Listened To: ${songsListenedTo} & Hours Listened To: ${hoursListened}`;
  document.getElementById("statsMobile").innerHTML =
    `Songs Listened To: ${songsListenedTo}<br>Hours Listened To: ${hoursListened}`;
}
