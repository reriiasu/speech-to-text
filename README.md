# speech-to-text

Real-time transcription using [faster-whisper](https://github.com/guillaumekln/faster-whisper)

![use animation](docs/UseAnimation.gif)

## Installation

1. pip install .

## Usage

1. python -m speech_to_text
1. Select "App Settings" and configure the settings.
1. Select "Model Settings" and configure the settings.
1. Select "Transcribe Settings" and configure the settings.
1. Select "VAD Settings" and configure the settings.
1. Start Transcription

## Notes

- If you select local_model in "Model size or path", the model with the same name in the local folder will be referenced.
- I haven't validated the parameters because I don't know the proper value for 'Whisper' or 'faster-whisper'.
  Check the error message displayed on the console.

## Todo

- [x] Save and load previous settings.

- [x] Use Silero VAD

- [x] Allow local parameters to be set from the GUI.
