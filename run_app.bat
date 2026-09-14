@echo off
chcp 949 > nul
cd /d "%~dp0"
title Real Estate vs Stock Return Comparison Dashboard

echo ===================================================
echo   부동산 vs 주식 투자 수익률 비교 대시보드
echo ===================================================
echo.

REM 가상환경 자동 활성화 (존재 시)
if exist ".venv\Scripts\activate.bat" (
    echo [가상환경] .venv 활성화 중...
    call ".venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    echo [가상환경] venv 활성화 중...
    call "venv\Scripts\activate.bat"
)

REM Python 설치 확인
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [오류] Python이 시스템에 설치되어 있지 않거나 PATH 환경 변수에 등록되어 있지 않습니다.
    echo Python을 설치하거나 환경 변수를 확인해 주세요.
    echo.
    pause
    exit /b 1
)

echo 대시보드 앱을 시작합니다...
echo - 로컬 주소: http://localhost:8501
echo - 기본 웹 브라우저가 자동으로 실행됩니다.
echo - 앱을 종료하려면 이 창에서 [Ctrl + C]를 누르세요.
echo.

python -m streamlit run app.py %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [알림] 앱 실행이 중단되었습니다. (종료 코드: %ERRORLEVEL%)
    echo.
)

pause
