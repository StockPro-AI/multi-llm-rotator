@echo off
setlocal EnableDelayedExpansion

:: ================================================================
:: multi-llm-rotator -- One-Click Windows Setup
:: ================================================================
:: - Checks Docker availability
:: - Checks if .env exists, creates from .env.example if not
:: - Auto-detects port conflicts and falls back to alternatives
:: - Builds the Docker image and starts the container
:: ================================================================

title multi-llm-rotator Setup
color 0A

echo.
echo  ============================================================
echo   multi-llm-rotator -- One-Click Docker Setup
echo  ============================================================
echo.

:: ----------------------------------------------------------------
:: 1. Check Docker is installed
:: ----------------------------------------------------------------
echo [1/5] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Docker is not installed or not in PATH.
    echo  Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Docker daemon is not running.
    echo  Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker is running.

:: ----------------------------------------------------------------
:: 2. Check docker compose (v2) is available
:: ----------------------------------------------------------------
echo [2/5] Checking Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Docker Compose v2 not found.
    echo  Please update Docker Desktop to a recent version.
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker Compose v2 found.

:: ----------------------------------------------------------------
:: 3. Ensure .env file exists
:: ----------------------------------------------------------------
echo [3/5] Checking .env file...
if not exist .env (
    if exist .env.example (
        echo  [INFO] .env not found. Copying from .env.example...
        copy /Y .env.example .env >nul
        echo.
        echo  *** ACTION REQUIRED ***
        echo  Please edit .env and add your real API keys before continuing.
        echo  File location: %CD%\.env
        echo.
        pause
    ) else (
        echo  [WARN] Neither .env nor .env.example found. Continuing without env file.
        echo  Make sure you set API keys manually in docker-compose.yml or environment.
    )
) else (
    echo  [OK] .env file found.
)

:: ----------------------------------------------------------------
:: 4. Auto-detect free port with fallback list
:: ----------------------------------------------------------------
echo [4/5] Checking port availability...

:: Primary port + ordered fallback list
set "PORTS=8765 8766 8767 8768 8769 9000 9001 9002"
set "CHOSEN_PORT="

for %%P in (%PORTS%) do (
    if "!CHOSEN_PORT!"=="" (
        :: netstat -ano lists active connections; find port %%P in LISTENING state
        netstat -ano 2>nul | findstr /C ":%%P " | findstr /I "LISTENING" >nul 2>&1
        if errorlevel 1 (
            :: Port is free
            set "CHOSEN_PORT=%%P"
            echo  [OK] Port %%P is available -- using it.
        ) else (
            echo  [SKIP] Port %%P is already in use. Trying next...
        )
    )
)

if "!CHOSEN_PORT!"=="" (
    echo.
    echo  [ERROR] All fallback ports are occupied: %PORTS%
    echo  Please free one of these ports and try again.
    echo.
    pause
    exit /b 1
)

:: Write chosen port into environment for docker compose
set "LLM_PORT=!CHOSEN_PORT!"

:: ----------------------------------------------------------------
:: 5. Build and start container
:: ----------------------------------------------------------------
echo [5/5] Building Docker image and starting container...
echo  Port mapping: !LLM_PORT! -^> 8765 (container)
echo.

docker compose up --build -d
if errorlevel 1 (
    echo.
    echo  [ERROR] docker compose failed. Check the output above for details.
    echo.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: Done!
:: ----------------------------------------------------------------
echo.
echo  ============================================================
echo   Setup complete!
echo  ============================================================
echo   Container : multi-llm-rotator
echo   Port      : !LLM_PORT! (host) -^> 8765 (container)
echo   Status    : docker ps --filter name=multi-llm-rotator
echo   Logs      : docker logs -f multi-llm-rotator
echo   Stop      : docker compose down
echo  ============================================================
echo.
pause
endlocal
