eel.expose(on_recive_message);
function on_recive_message(message) {
  addMessage("console-message", message);
}

eel.expose(display_transcription);
function display_transcription(transcript) {
  addMessage("transcription", transcript);
}

eel.expose(on_recive_segments);
function on_recive_segments(segments) {
  clearMessage("transcription");
  const audio = document.querySelector("#audio-control");
  audio.src = "voice.wav" + "?v=" + new Date().getTime();
  audio.hidden = false;
  audio.load();

  const transcription = document.querySelector(`#transcription`);
  for (let i = 0; i < segments.length; i++) {
    const newel = document.createElement("div");
    newel.textContent = segments[i]["text"];
    newel.setAttribute("data-start", segments[i]["start"]);
    newel.setAttribute("data-end", segments[i]["end"]);

    newel.addEventListener("click", onClickTranscription);

    transcription.appendChild(newel);
  }
}

eel.expose(transcription_stoppd);
function transcription_stoppd() {
  document.querySelector("#start-button").disabled = false;
  document.querySelector("#stop-button").disabled = true;
  enableSettingControle();
}

function addMessage(elementId, message) {
  const el = document.querySelector(`#${elementId}`);
  const newel = document.createElement("div");
  newel.textContent = message;
  el.appendChild(newel);

  el.scrollTop = el.scrollHeight;
}

function onClickTranscription(event) {
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
  menuClose();
  disableSettingControle();
  document.querySelector("#start-button").disabled = true;
  document.querySelector("#stop-button").disabled = false;
  clearAudioControl();
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
  await eel.stop_transcription();
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

  document.querySelector("#start-button").addEventListener("click", () => {
    startTranscription();
  });
  document.querySelector("#stop-button").addEventListener("click", () => {
    stopTranscription();
  });

  document
    .querySelector("#transcription-copy")
    .addEventListener("click", () => {
      copyToClipboard("transcription");
    });
  document
    .querySelector("#transcription-clear")
    .addEventListener("click", () => {
      clearAudioControl();
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

  audio.addEventListener("timeupdate", (event) => {
    const currentTime = event.target.currentTime;
    const subtitles = Array.from(
      document.querySelector("#transcription").children
    );

    subtitles.forEach((subtitle) => {
      const start = parseFloat(subtitle.getAttribute("data-start"));
      const end = parseFloat(subtitle.getAttribute("data-end"));

      if (currentTime >= start && currentTime <= end) {
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

function clearAudioControl() {
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
