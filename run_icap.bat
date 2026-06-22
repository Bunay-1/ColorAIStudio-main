@echo off
setlocal enabledelayedexpansion
title ICAP Industrial Color AI Platform v8.9.1 Enterprise
color 0A

echo ===================================================
echo   Industrial Color AI Platform (ICAP) - Launcher
echo   Version: 8.9.1 ^| Enterprise Edition
echo ===================================================
echo.

REM Set working directory
cd /d "%~dp0"

REM 1. Check for Python
echo [*] Проверка за инсталиран Python...
set "PYTHON_CMD="

REM Try to find python.exe
for %%i in (python.exe python3.exe py.exe) do (
    where %%i >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        REM Verify it's actually working and not just a Windows Store shortcut
        %%i --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "PYTHON_CMD=%%i"
            goto :found_python
        )
    )
)

:found_python
if not defined PYTHON_CMD (
    echo [!] ГРЕШКА: Python не е намерен в PATH.
    echo Моля инсталирайте Python 3.10+ от python.org и опитайте отново.
    echo Уверете се, че сте избрали "Add Python to PATH" при инсталацията.
    pause
    exit /b 1
)

echo [*] Намерен Python: !PYTHON_CMD!

REM 2. Setup environment
if not exist .env (
    if exist .env.example (
        echo [*] Създаване на .env от .env.example...
        copy .env.example .env >nul
    ) else (
        echo [!] ВНИМАНИЕ: .env файл липсва и .env.example не е намерен.
    )
)

REM 3. Virtual Environment Setup
if not exist .venv (
    echo [*] Създаване на виртуална среда (.venv)...
    "!PYTHON_CMD!" -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo [!] ГРЕШКА при създаване на виртуалната среда.
        pause
        exit /b 1
    )
)

REM 4. Determine Venv Python path
set "VENV_PYTHON=.venv\Scripts\python.exe"
if not exist "!VENV_PYTHON!" (
    set "VENV_PYTHON=.venv\bin\python"
)

if not exist "!VENV_PYTHON!" (
    echo [!] ГРЕШКА: Не бе намерен изпълним файл на Python във виртуалната среда.
    echo Опитайте се да изтриете папка .venv и стартирайте скрипта отново.
    pause
    exit /b 1
)

REM 5. Dependencies
echo [*] Обновяване на pip и инсталиране на зависимости...
"!VENV_PYTHON!" -m pip install --upgrade pip
if exist "requirements.txt" (
    "!VENV_PYTHON!" -m pip install -r requirements.txt
) else (
    echo [!] ГРЕШКА: requirements.txt не е намерен! Сървърът може да не стартира.
)

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [!] ВНИМАНИЕ: Имаше грешки при инсталиране на зависимостите.
    echo Проверете интернет връзката си и опитайте отново.
    echo Натиснете произволен клавиш, за да опитате да стартирате сървъра въпреки това...
    pause >nul
)

REM 6. Start Server
if not exist "irm_api.py" (
    echo [!] ГРЕШКА: Основният файл irm_api.py не е намерен в текущата директория: %cd%
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   ICAP API Сървърът стартира...
echo   Dashboard: Отворете irm_dashboard.html в браузъра
echo   URL: http://localhost:8000
echo ===================================================
echo.

"!VENV_PYTHON!" irm_api.py

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [!] Сървърът спря неочаквано (Code: !ERRORLEVEL!).
    echo Проверете логовете по-горе за повече информация.
    pause
)
pause
