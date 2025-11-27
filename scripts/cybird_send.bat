@echo off
chcp 65001 >nul
title CybirdWatching CLI - 发送命令

if "%~1"=="" (
    echo ======================================
    echo   CybirdWatching CLI 命令发送器
    echo ======================================
    echo.
    echo 使用方法: %~nx0 "命令" [端口] [波特率]
    echo.
    echo 示例:
    echo   %~nx0 "log"                    - 发送log命令
    echo   %~nx0 "status" COM4            - 发送status命令到COM4
    echo   %~nx0 "log lines 50" COM4 9600 - 发送命令到COM4，波特率9600
    echo.
    pause
    exit /b 1
)

REM 检查是否在正确目录
if not exist "cybird_watching_cli\src\cybird_watching_cli\main.py" (
    echo 错误: 找不到cybird_watching_cli目录
    pause
    exit /b 1
)

set COMMAND=%~1
set PORT=%~2
set BAUD=%~3

echo 发送命令: %COMMAND%
if not "%PORT%"=="" (
    echo 端口: %PORT%
    if not "%BAUD%"=="" (
        echo 波特率: %BAUD%
    )
)
echo.

REM 进入CLI目录
cd /d cybird_watching_cli

REM 检查uv是否安装
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到uv包管理器
    pause
    exit /b 1
)

REM 构建命令
set CMD_ARGS=send "%COMMAND%"

if not "%PORT%"=="" (
    set CMD_ARGS=%CMD_ARGS% --port %PORT%
)

if not "%BAUD%"=="" (
    set CMD_ARGS=%CMD_ARGS% --baudrate %BAUD%
)

REM 执行命令
uv run python -m cybird_watching_cli.main %CMD_ARGS%

echo.
pause