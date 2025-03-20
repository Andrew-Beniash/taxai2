@echo off
REM A script to build and run the Tax Law Assistant backend locally on Windows

REM Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
  echo ERROR: OPENAI_API_KEY environment variable is not set.
  echo Please set it with: set OPENAI_API_KEY=your_api_key
  exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

echo Building the Tax Law Assistant backend...
call mvn clean package -DskipTests

if %ERRORLEVEL% EQU 0 (
  echo Build successful. Starting the application...
  java -jar target\tax-law-assistant-1.0.0-SNAPSHOT.jar
) else (
  echo Build failed. Please check the error messages above.
  exit /b 1
)
