@echo off
REM Name of the virtual environment directory
set VENV_DIR=myenv

REM Check if the virtual environment already exists
if exist %VENV_DIR% (
    echo Virtual environment '%VENV_DIR%' already exists.
    
    REM Activate the virtual environment
    call %VENV_DIR%\Scripts\activate
    
    REM Check if requirements.txt exists and update packages
    if exist requirements.txt (
        echo Updating packages from requirements.txt...
        pip install -r requirements.txt
        echo Packages updated.
    ) else (
        echo requirements.txt not found.
    )
) else (
    REM Create the virtual environment
    python -m venv %VENV_DIR%
    echo Virtual environment '%VENV_DIR%' created.

    REM Activate the virtual environment and install local packages
    call %VENV_DIR%\Scripts\activate
    echo Installing local packages...
    pip install .
    echo Local packages installed.
)

REM Run python -m speech_to_text
echo Running python -m speech_to_text...
python -m speech_to_text

REM Keep the command prompt open
cmd /K