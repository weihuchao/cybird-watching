@echo off
chcp 65001 >nul
title CybirdWatching CLI

echo ======================================
echo   CybirdWatching CLI 带参数启动器
echo ======================================
echo.

REM 检查是否在正确目录
if not exist "cybird_watching_cli\src\cybird_watching_cli\main.py" (
    echo 错误: 找不到cybird_watching_cli目录
    echo 请确保此bat文件位于scripts目录中
    pause
    exit /b 1
)

REM 显示使用说明
echo 使用方法:
echo   %~nx0                           - 使用默认配置 (COM3, 115200)
echo   %~nx0 COM4                      - 指定端口
echo   %~nx0 COM4 9600                 - 指定端口和波特率
echo   %~nx0 help                      - 显示帮助
echo.

REM 进入CLI目录
cd /d cybird_watching_cli

REM 检查uv是否安装
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到uv包管理器
    echo 请先安装uv: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

REM 解析参数
set PORT=%1
set BAUD=%2

REM 如果没有参数，使用默认值启动交互模式
if "%~1"=="" (
    echo 正在启动交互模式 (默认端口 COM3, 波特率 115200)...
    echo.
    uv run python -m cybird_watching_cli.main
    goto :end
)

REM 如果第一个参数是help，显示帮助
if /i "%~1"=="help" (
    echo 显示帮助信息:
    echo.
    uv run python -m cybird_watching_cli.main --help
    goto :end
)

REM 如果有端口参数
if not "%PORT%"=="" (
    if not "%BAUD%"=="" (
        echo 正在启动 (端口: %PORT%, 波特率: %BAUD%)...
        echo.
        uv run python -m cybird_watching_cli.main --port %PORT% --baudrate %BAUD%
    ) else (
        echo 正在启动 (端口: %PORT%)...
        echo.
        uv run python -m cybird_watching_cli.main --port %PORT%
    )
) else (
    echo 正在启动交互模式...
    echo.
    uv run python -m cybird_watching_cli.main
)

:end
echo.
echo 感谢使用CybirdWatching CLI！
pause