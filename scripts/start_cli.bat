@echo off
chcp 65001 >nul
title CybirdWatching CLI

echo.
echo ================================================================
echo                    CybirdWatching CLI Launcher
echo ================================================================
echo.
echo Starting interactive command line tool...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0cybird_watching_cli.ps1"

echo.
echo CLI has exited
pause