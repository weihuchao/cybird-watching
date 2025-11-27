@echo off
chcp 65001 >nul
title HoloCubic CLI

echo.
echo ================================================================
echo                    HoloCubic CLI Launcher
echo ================================================================
echo.
echo Starting interactive command line tool...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0holocubic_cli.ps1"

echo.
echo CLI has exited
pause