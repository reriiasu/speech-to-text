eel.expose(on_recive_message);
function on_recive_message(message) {
  const messageArea = document.getElementById("console-message");
  messageArea.textContent += message + "\n";

  messageArea.scrollTop = messageArea.scrollHeight;
}

eel.expose(display_transcription);
function display_transcription(transcript) {
  const transcriptArea = document.getElementById("transcription");
  transcriptArea.innerText += transcript + "\n";

  transcriptArea.scrollTop = transcriptArea.scrollHeight;
}

eel.expose(transcription_stoppd);
function transcription_stoppd() {
  document.getElementById("start-button").disabled = false;
  document.getElementById("stop-button").disabled = true;
  enableSettingControle();
}

async function updateDevices() {
  let devices = await eel.get_valid_devices()();
  let select = document.getElementById("audio-device-select");
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

function getModelSettings() {
  const settings = getContentSettings("#model-settings-content");

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
  const settings = getContentSettings("#transcribe-settings-content");

  const temperature = settings["temperature"];
  if (/^(\d*\.?\d+|((\d*\.?\d+,)+\d*\.?\d+))$/.test(temperature)) {
    let numbers = 0;
    if (temperature.includes(",")) {
      numbers = temperature.split(",").map(Number);
    } else {
      numbers = Number(temperature);
    }
    settings["temperature"] = numbers;
  }

  const suppress_tokens = settings["suppress_tokens"];
  if (/^(-?\d+|(-?\d+,)+-?\d+)$/.test(suppress_tokens)) {
    let numbers = 0;
    if (suppress_tokens.includes(",")) {
      numbers = suppress_tokens.split(",").map(Number);
    } else {
      numbers = [Number(suppress_tokens)];
    }
    settings["suppress_tokens"] = numbers;
  }
  return settings;
}

function startTranscription() {
  disableSettingControle();
  document.getElementById("start-button").disabled = true;
  document.getElementById("stop-button").disabled = false;

  const selectedAudioDeviceIndex = document.getElementById(
    "audio-device-select"
  ).selectedIndex;
  const modelSettings = getModelSettings();
  const transcribeSettings = getTranscribeSettings();

  eel.start_transcription(
    selectedAudioDeviceIndex,
    modelSettings,
    transcribeSettings
  );
}

async function stopTranscription() {
  await eel.stop_transcription();
}

function createDropdownOptions(data, dropdownId) {
  const select = document.getElementById(dropdownId);
  for (const key in data) {
    const option = document.createElement("option");
    option.value = key;
    option.text = data[key];
    select.appendChild(option);
  }
}

window.addEventListener("load", (event) => {
  updateDevices();
  eel.get_dropdown_options()(function (dropdownOptions) {
    createDropdownOptions(dropdownOptions["model_sizes"], "model_size_or_path");
    createDropdownOptions(dropdownOptions["compute_types"], "compute_type");
    createDropdownOptions(dropdownOptions["languages"], "language");
  });

  const menus = document.querySelectorAll(".menu");
  const contents = document.querySelectorAll(".content-window");

  menus.forEach((menu) => {
    menu.addEventListener("click", () => {
      const id = menu.getAttribute("id");
      const targetContents = document.querySelectorAll(`#${id}-content`);

      contents.forEach((c) => {
        c.hidden = true;
        const inner = c.querySelector(".content-inner");
        inner.classList.remove("open");
      });

      // If the menu is active, close it
      if (menu.classList.contains("active")) {
        menu.classList.remove("active");
        return;
      }

      menus.forEach((t) => t.classList.remove("active"));
      menu.classList.add("active");

      targetContents.forEach((c) => {
        c.hidden = false;
        const innerContent = c.querySelector(".content-inner");
        requestAnimationFrame(() => {
          innerContent.classList.add("open");
        });
      });
    });
  });

  const closeIcons = Array.from(document.querySelectorAll(".close-icon"));

  closeIcons.forEach((icon) => {
    icon.addEventListener("click", (e) => {
      contents.forEach((c) => {
        c.hidden = true;
        const inner = c.querySelector(".content-inner");
        inner.classList.remove("open");
      });
      menus.forEach((t) => t.classList.remove("active"));
    });
  });
});

function copyToClipboard(elementId) {
  const transcriptionElement = document.getElementById(elementId);
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
  const toastElement = document.getElementById("toast");
  toastElement.classList.add("show");

  setTimeout(function () {
    toastElement.classList.remove("show");
  }, 3000);
}

function clearMessage(elementId) {
  const transcriptElement = document.querySelector(
    `#${elementId}.message-area`
  );
  transcriptElement.textContent = "";
}

function disableSettingControle() {
  let elements = document.getElementsByClassName("setting-control");

  for (var i = 0; i < elements.length; i++) {
    elements[i].disabled = true;
  }
}

function enableSettingControle() {
  let elements = document.getElementsByClassName("setting-control");

  for (var i = 0; i < elements.length; i++) {
    elements[i].disabled = false;
  }
}
