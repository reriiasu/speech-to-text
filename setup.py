from setuptools import setup, find_packages


def read_requirements():
    with open("requirements.txt") as req:
        return [i.strip() for i in req]


setup(
    name="speech-to-text",
    version="0.3.6",
    description="Real-time transcription using faster-whisper",
    author="reriiasu",
    url="https://github.com/reriiasu/speech-to-text",
    packages=find_packages(),
    install_requires=read_requirements(),
)
