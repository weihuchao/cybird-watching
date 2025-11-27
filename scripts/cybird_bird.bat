@echo off
chcp 65001 >nul
title CybirdWatching CLI - 观鸟模式

echo ======================================
echo   CybirdWatching CLI 观鸟工具
echo ======================================
echo.

REM 检查参数
if "%1"=="" goto :show_help
if "%1"=="help" goto :show_help
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

REM 检查是否在正确目录
if not exist "cybird_watching_cli\src\cybird_watching_cli\main.py" (
    echo 错误: 找不到cybird_watching_cli目录
    echo 请确保此bat文件位于scripts目录中
    pause
    exit /b 1
)

echo 正在执行观鸟命令: %1
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

REM 设置默认端口
set PORT=COM3
if not "%2"=="" set PORT=%2

REM 执行bird命令
uv run python -m cybird_watching_cli.main send "bird %1" --port %PORT%

echo.
echo 观鸟命令执行完成！
pause
exit /b 0

:show_help
echo.
echo CybirdWatching CLI 观鸟工具使用说明：
echo.
echo 用法:
echo   cybird_bird.bat ^<command^> [port]
echo.
echo 观鸟命令:
echo   trigger    - 手动触发小鸟动画
echo   stats      - 显示观鸟统计信息
echo   reset      - 重置观鸟统计数据
echo   list       - 显示可用小鸟列表
echo.
echo 示例:
echo   cybird_bird.bat trigger        # 触发小鸟动画
echo   cybird_bird.bat stats          # 查看统计
echo   cybird_bird.bat trigger COM4   # 在COM4端口触发小鸟
echo   cybird_bird.bat reset          # 重置统计数据
echo.
pause