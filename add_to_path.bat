@echo off
setlocal

:: 現在のディレクトリ（tough.batがある場所）をPATHに追加
set "TOUGH_BIN=%~dp0"

echo Adding %TOUGH_BIN% to user PATH environment variable...
setx PATH "%PATH%;%TOUGH_BIN%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Path added successfully!
    echo Please restart your command prompt or PowerShell to use the 'tough' command.
) else (
    echo.
    echo Failed to add path. You might need to run this as Administrator.
)

pause
