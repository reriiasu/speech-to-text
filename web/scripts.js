eel.expose(on_recive_message);
function on_recive_message(message) {
  document.querySelector("#loading-screen").classList.remove("show");
  addMessage("console-message", message);
}

eel.expose(display_transcription);
function display_transcription(transcript) {
  addMessage("transcription", transcript);
}

eel.expose(transcription_clear);
function transcription_clear() {
  clearMessage("transcription");
}

eel.expose(on_recive_segments);
function on_recive_segments(segments) {
  document.querySelector("#loading-screen").classList.remove("show");

  const audio = document.querySelector("#audio-control");

  const appSettings = getAppSettings();
  if (appSettings["create_audio_file"]) {
    audio.src = "voice.wav" + "?v=" + new Date().getTime();
    audio.hidden = false;
    audio.load();
  }

  const srt = document.querySelector("#create-srt");
  srt.classList.remove("hidden");

  const transcription = document.querySelector(`#transcription`);
  for (let i = 0; i < segments.length; i++) {
    const words = segments[i]["words"];
    const start = segments[i]["start"];
    const end = segments[i]["end"];

    const block = document.createElement("div");
    block.classList.add("segment-container");

    const label = document.createElement("label");
    label.classList.add("time-label");
    label.textContent = `[${formatTime(start)} --> ${formatTime(end)}]`;
    block.appendChild(label);

    if (words.length !== 0) {
      for (let j = 0; j < words.length; j++) {
        const text = words[j]["text"];
        const wordStart = words[j]["start"];
        const wordEnd = words[j]["end"];

        const span = document.createElement("span");
        span.textContent = text;
        span.setAttribute("data-start", wordStart);
        span.setAttribute("data-end", wordEnd);
        span.addEventListener("click", onClickSegment);
        block.appendChild(span);
      }
    } else {
      const text = segments[i]["text"];

      const span = document.createElement("span");
      span.textContent = text;
      span.setAttribute("data-start", start);
      span.setAttribute("data-end", end);
      span.addEventListener("click", onClickSegment);
      block.appendChild(span);
    }

    transcription.appendChild(block);
  }
}

eel.expose(transcription_stoppd);
function transcription_stoppd() {
  document.querySelector("#start-button").classList.remove("hidden");
  document.querySelector("#stop-button").classList.add("hidden");
  enableSettingControle();
  enableModeControle();
}

eel.expose(transcription_stoppd2);
function transcription_stoppd2() {
  document.querySelector("#start-button").classList.remove("hidden");
  document.querySelector("#stop-button").classList.add("hidden");
  enableSettingControle();
}

function addMessage(elementId, message) {
  const el = document.querySelector(`#${elementId}`);
  const newel = document.createElement("div");
  newel.classList.add("segment-container");
  newel.textContent = message;
  el.appendChild(newel);

  el.scrollTop = el.scrollHeight;
}

function onClickSegment(event) {
  const audio = document.querySelector("#audio-control");
  audio.currentTime = event.target.getAttribute("data-start");
  audio.play();
}

async function updateDevices() {
  let devices = await eel.get_valid_devices()();
  let select = document.querySelector("#audio_device");
  select.innerHTML = "";
  for (let i = 0; i < devices.length; i++) {
    let opt = document.createElement("option");
    opt.value = devices[i].index;
    opt.innerHTML = devices[i].name;
    select.appendChild(opt);
  }
}

function getContentSettings(elementid) {
  let elements = Array.from(
    document.querySelector(elementid).querySelectorAll(".setting-control")
  );

  const json = elements.reduce((obj, element) => {
    let value;
    if (element.tagName === "SELECT") {
      value = element.options[element.selectedIndex].value;
    } else if (element.tagName === "INPUT" && element.type === "checkbox") {
      value = element.checked;
    } else if (element.tagName === "INPUT" && element.type === "number") {
      value = Number(element.value);
    } else {
      value = element.value;
    }

    // If the value is empty and optional
    if (value === "" && document.querySelector(".optional") !== null) {
      return obj;
    }
    obj[element.id] = value;
    return obj;
  }, {});

  return json;
}

function getAppSettings() {
  const settings = getContentSettings("#app-settings-window");
  settings["audio_device"] =
    document.querySelector("#audio_device").selectedIndex;

  return settings;
}

function getModelSettings() {
  const settings = getContentSettings("#model-settings-window");

  const deviceIndex = settings["device_index"];
  if (/^(\d+|(\d+,)+\d+)$/.test(deviceIndex)) {
    let numbers = 0;
    if (deviceIndex.includes(",")) {
      numbers = deviceIndex.split(",").map(Number);
    } else {
      numbers = Number(deviceIndex);
    }
    settings["device_index"] = numbers;
  }

  return settings;
}

function getTranscribeSettings() {
  const transcribeSettings = getContentSettings("#transcribe-settings-window");
  const vadSettings = getContentSettings("#vad-settings-window");

  const temperature = transcribeSettings["temperature"];
  if (/^(\d*\.?\d+|((\d*\.?\d+,)+\d*\.?\d+))$/.test(temperature)) {
    let numbers = 0;
    if (temperature.includes(",")) {
      numbers = temperature.split(",").map(Number);
    } else {
      numbers = Number(temperature);
    }
    transcribeSettings["temperature"] = numbers;
  }

  const suppress_tokens = transcribeSettings["suppress_tokens"];
  if (/^(-?\d+|(-?\d+,)+-?\d+)$/.test(suppress_tokens)) {
    let numbers = 0;
    if (suppress_tokens.includes(",")) {
      numbers = suppress_tokens.split(",").map(Number);
    } else {
      numbers = [Number(suppress_tokens)];
    }
    transcribeSettings["suppress_tokens"] = numbers;
  }
  transcribeSettings["vad_filter"] = vadSettings["vad_filter"];
  delete vadSettings["vad_filter"];
  transcribeSettings["vad_parameters"] = vadSettings;

  return transcribeSettings;
}

function startTranscription() {
  document.querySelector("#loading-screen").classList.add("show");
  menuClose();
  disableModeControle();
  disableSettingControle();

  document.querySelector("#start-button").classList.add("hidden");
  document.querySelector("#stop-button").classList.remove("hidden");
  hideCreateSrt();
  hideAudioControl();
  clearMessage("transcription");

  const appSettings = getAppSettings();
  const modelSettings = getModelSettings();
  const transcribeSettings = getTranscribeSettings();

  eel.start_transcription({
    app_settings: appSettings,
    model_settings: modelSettings,
    transcribe_settings: transcribeSettings,
  });
}

async function stopTranscription() {
  document.querySelector("#loading-screen").classList.add("show");
  await eel.stop_transcription();
}

function audioTranscription() {
  const fileInput = document.querySelector("#audio-file");
  const file = fileInput.files[0];

  if (!fileValidation(file)) {
    return;
  }
  document.querySelector("#loading-screen").classList.add("show");
  menuClose();

  hideCreateSrt();
  hideAudioControl();
  clearMessage("transcription");

  const appSettings = getAppSettings();
  const modelSettings = getModelSettings();
  const transcribeSettings = getTranscribeSettings();

  const reader = new FileReader();
  reader.onload = function (e) {
    const data = new Uint8Array(e.target.result);
    eel.audio_transcription(
      {
        app_settings: appSettings,
        model_settings: modelSettings,
        transcribe_settings: transcribeSettings,
      },
      Array.from(data)
    );
  };
  reader.readAsArrayBuffer(file);
}

function fileValidation(file) {
  if (!file) {
    on_recive_message("No file chosen");
    return false;
  }

  const maxSizeInMB = 10;
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  if (file.size > maxSizeInBytes) {
    on_recive_message(`File size must be under ${maxSizeInMB}MB`);
    return false;
  }
  return true;
}

function realTimeMode() {
  document.querySelector("#real-time-mode").classList.add("selected");
  document.querySelector("#audio-mode").classList.remove("selected");

  document.querySelector("#start-button").classList.remove("hidden");

  document.querySelector("#audio-transcription").classList.add("hidden");
  document.querySelector("#audio-file").classList.add("hidden");
}

function audioMode() {
  document.querySelector("#real-time-mode").classList.remove("selected");
  document.querySelector("#audio-mode").classList.add("selected");

  document.querySelector("#start-button").classList.add("hidden");

  document.querySelector("#audio-transcription").classList.remove("hidden");
  document.querySelector("#audio-file").classList.remove("hidden");
}

function createDropdownOptions(options, elementId) {
  const select = document.querySelector(`#${elementId}`);
  for (const key in options) {
    const option = document.createElement("option");
    option.value = key;
    option.text = options[key];
    select.appendChild(option);
  }
}

function setContentSettings(settings, elementid) {
  if (settings === undefined) {
    return;
  }

  const elements = Array.from(
    document.querySelector(elementid).querySelectorAll(".setting-control")
  );

  for (let element of elements) {
    if (!(element.id in settings)) {
      continue;
    }

    if (Array.isArray(settings[element.id])) {
      element.value = settings[element.id].join(",");
    } else if (element.tagName === "INPUT" && element.type === "checkbox") {
      element.checked = settings[element.id];
    } else {
      element.value = settings[element.id];
    }
  }
}

function setDropdownOptions() {
  eel.get_dropdown_options()(function (dropdownOptions) {
    createDropdownOptions(dropdownOptions["model_sizes"], "model_size_or_path");
    createDropdownOptions(dropdownOptions["compute_types"], "compute_type");
    createDropdownOptions(dropdownOptions["languages"], "language");
  });
}

function setUserSettings() {
  eel.get_user_settings()(function (userSettings) {
    setContentSettings(userSettings["app_settings"], "#app-settings-window");
    setContentSettings(
      userSettings["model_settings"],
      "#model-settings-window"
    );
    setContentSettings(
      userSettings["transcribe_settings"],
      "#transcribe-settings-window"
    );
    setContentSettings(
      Object.assign(
        {},
        userSettings["transcribe_settings"],
        userSettings["transcribe_settings"]["vad_parameters"]
      ),
      "#vad-settings-window"
    );
  });
}

function onClickMenu(el) {
  if (el.classList.contains("active")) {
    menuClose();
    return;
  }
  menuClose();

  el.classList.add("active");

  const targetWindow = document.querySelector(`#${el.id}-window`);
  targetWindow.hidden = false;
  const inner = targetWindow.querySelector(".menu-window-inner");
  requestAnimationFrame(() => {
    inner.classList.add("open");
  });
}

function menuClose() {
  const menus = document.querySelectorAll(".menu");
  const menuWindows = document.querySelectorAll(".menu-window");
  menuWindows.forEach((w) => {
    w.hidden = true;
    const inner = w.querySelector(".menu-window-inner");
    inner.classList.remove("open");
  });
  menus.forEach((t) => t.classList.remove("active"));
}

function addButtonClickEventListener() {
  const menus = document.querySelectorAll(".menu");
  menus.forEach((menu) => {
    menu.addEventListener("click", () => {
      onClickMenu(menu);
    });
  });

  const closeIcons = document.querySelectorAll(".close-icon");
  closeIcons.forEach((icon) => {
    icon.addEventListener("click", () => {
      menuClose();
    });
  });

  document
    .querySelector("#real-time-mode")
    .addEventListener("click", function () {
      realTimeMode();
    });

  document.querySelector("#audio-mode").addEventListener("click", function () {
    audioMode();
  });

  document.querySelector("#start-button").addEventListener("click", () => {
    startTranscription();
  });
  document.querySelector("#stop-button").addEventListener("click", () => {
    stopTranscription();
  });
  document
    .querySelector("#audio-transcription")
    .addEventListener("click", () => {
      audioTranscription();
    });

  document.querySelector("#create-srt").addEventListener("click", () => {
    createSrt();
  });

  document
    .querySelector("#transcription-copy")
    .addEventListener("click", () => {
      copyToClipboard("transcription");
    });
  document
    .querySelector("#transcription-clear")
    .addEventListener("click", () => {
      hideCreateSrt();
      hideAudioControl();
      clearMessage("transcription");
    });

  document
    .querySelector("#console-message-copy")
    .addEventListener("click", () => {
      copyToClipboard("console-message");
    });
  document
    .querySelector("#console-message-clear")
    .addEventListener("click", () => {
      clearMessage("console-message");
    });
}

function addTimeupdateEventListener() {
  const audio = document.querySelector(`#audio-control`);
  // Define the time extension to avoid skipping subtitle highlighting
  const timeExtension = 0.2;

  audio.addEventListener("timeupdate", (event) => {
    const currentTime = event.target.currentTime;
    const subtitles = document.querySelectorAll("#transcription span");

    subtitles.forEach((subtitle) => {
      const start = parseFloat(subtitle.getAttribute("data-start"));
      const end = parseFloat(subtitle.getAttribute("data-end"));

      // Add the time extension to the end time
      if (currentTime >= start && currentTime <= end + timeExtension) {
        subtitle.classList.add("highlight");
      } else {
        subtitle.classList.remove("highlight");
      }
    });
  });
}

window.addEventListener("load", (event) => {
  updateDevices();
  setDropdownOptions();
  setUserSettings();
  addButtonClickEventListener();
  addTimeupdateEventListener();
});

function copyToClipboard(elementId) {
  const transcriptionElement = document.querySelector(`#${elementId}`);
  const text = transcriptionElement.innerText;
  navigator.clipboard.writeText(text).then(
    function () {
      showToast();
    },
    function (err) {
      console.error("Could not copy text: ", err);
    }
  );
}

function downloadSRTFile(content, filename) {
  const blob = new Blob([content], { type: "text/srt" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.download = filename;
  link.href = url;

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function getSegmentsFromHTML() {
  const regex = /\[(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\](.+)/;
  const segmentContainers = document.querySelectorAll(".segment-container");
  const segments = new Map();

  segmentContainers.forEach((container) => {
    const match = container.innerText.match(regex);

    if (match) {
      const timestamp = match[1];
      const text = match[2].trim();
      segments.set(timestamp, text);
    }
  });

  return segments;
}

function createSrt() {
  const segments = getSegmentsFromHTML();
  const srtContent = createSRTContent(segments);
  downloadSRTFile(srtContent, "subtitles.srt");
}

function copyToClipboard(elementId) {
  const transcriptionElement = document.querySelector(`#${elementId}`);
  const text = transcriptionElement.innerText;
  navigator.clipboard.writeText(text).then(
    function () {
      showToast();
    },
    function (err) {
      console.error("Could not copy text: ", err);
    }
  );
}

function showToast() {
  const toastElement = document.querySelector("#toast");
  toastElement.classList.add("show");

  setTimeout(function () {
    toastElement.classList.remove("show");
  }, 3000);
}

function clearMessage(elementId) {
  const el = document.querySelector(`#${elementId}`);

  while (el.firstChild) {
    el.firstChild.remove();
  }
}

function hideCreateSrt() {
  const srt = document.querySelector("#create-srt");
  srt.classList.add("hidden");
}

function hideAudioControl() {
  const audio = document.querySelector("#audio-control");
  audio.pause();
  audio.src = "";
  audio.hidden = true;
}

function disableSettingControle() {
  let elements = document.querySelectorAll(".setting-control");

  for (var i = 0; i < elements.length; i++) {
    elements[i].disabled = true;
  }
}

function enableSettingControle() {
  let elements = document.querySelectorAll(".setting-control");

  for (var i = 0; i < elements.length; i++) {
    elements[i].disabled = false;
  }
}

function disableModeControle() {
  document.querySelector("#real-time-mode").disabled = true;
  document.querySelector("#audio-mode").disabled = true;
}

function enableModeControle() {
  document.querySelector("#real-time-mode").disabled = false;
  document.querySelector("#audio-mode").disabled = false;
}

function formatTime(timeInSeconds) {
  const hours = Math.floor(timeInSeconds / 3600);
  const minutes = Math.floor(timeInSeconds / 60) % 60;
  const seconds = Math.floor(timeInSeconds - hours * 3600 - minutes * 60);
  const milliseconds = Math.round((timeInSeconds % 1) * 1000);

  return `${pad(hours, 2)}:${pad(minutes, 2)}:${pad(seconds, 2)},${pad(
    milliseconds,
    3
  )}`;
}

function pad(num, size) {
  let s = num + "";
  while (s.length < size) {
    s = "0" + s;
  }
  return s;
}

function createSRTContent(segments) {
  return Array.from(segments.entries())
    .map(([key, value], index) => {
      return `${index + 1}\n${key}\n${value}\n`;
    })
    .join("\n");
}
