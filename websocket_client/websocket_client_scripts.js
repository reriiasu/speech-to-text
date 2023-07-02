document.addEventListener("DOMContentLoaded", function () {
  const webSocket = new WebSocket("ws://localhost:8765");

  webSocket.onopen = function () {
    console.log("WebSocket connection opened");
  };

  webSocket.onmessage = function (event) {
    console.log("WebSocket message received:", event.data);
    displayMessage(event.data);
  };

  webSocket.onclose = function () {
    console.log("WebSocket connection closed");
  };

  webSocket.onerror = function (event) {
    console.error("WebSocket error:", event);
  };

  function displayMessage(message) {
    const el = document.querySelector("#message");
    el.textContent = message;
  }
});
