@echo off
REM выводить только результат
chcp 65001 > nul
REM кодировка русских букв
echo ========================================
echo   JIRA Analytics Tool - Запуск
echo ========================================
echo.

REM Проверка наличия виртуального окружения
if not exist ".venv" (
    echo [INFO] Виртуальное окружение не найдено
    echo [INFO] Создаю виртуальное окружение...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Не удалось создать виртуальное окружение
        pause
        REM выход из скрипта в командную строку с кодом ошибки 1
        exit /b 1
    )
    echo [SUCCESS] Виртуальное окружение создано
)

REM Активация виртуального окружения
echo [INFO] Активация виртуального окружения...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Не удалось активировать виртуальное окружение
    pause
    exit /b 1
)

REM Проверка и установка зависимостей
echo [INFO] Проверка зависимостей...
if not exist "requirements.txt" (
    echo [ERROR] Файл requirements.txt не найден
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Не удалось установить зависимости
    pause
    exit /b 1
)

REM Запуск основной программы
echo.
echo [INFO] Запуск JIRA Analytics Tool...
echo ========================================
python src/main.py

REM Пауза для просмотра результатов
echo.
echo ========================================
echo Программа завершена. Нажмите любую клавишу...
pause > nul