@echo off
setlocal

:: python コマンドがどこにあるか確認
where /q python
if %ERRORLEVEL% neq 0 (
    echo Python が見つかりません。Python をインストールしてください。
    pause
    exit /b 1
)

:: main.py の絶対パスを取得
set "SCRIPT_DIR=%~dp0"
set "MAIN_SCRIPT=%SCRIPT_DIR%main.py"

:: ftype と assoc を設定（管理者権限が必要）
echo 管理者権限で実行してください...

:: .tough 拡張子に関連付け（tough.bat経由）
ftype TOUGHFile="%SCRIPT_DIR%tough.bat" "%%1" %%*
assoc .tough=TOUGHFile

if %ERRORLEVEL% equ 0 (
    echo.
    echo 関連付けが完了しました！
    echo hello.tough ファイルをダブルクリックするか、
    echo コマンドプロンプトで「hello.tough」と入力して実行できます。
) else (
    echo.
    echo エラーが発生しました。管理者権限で実行しているか確認してください。
)

pause
