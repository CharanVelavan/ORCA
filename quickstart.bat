@echo off
setlocal DisableDelayedExpansion
rem Run from the repository root even when invoked from another directory.
pushd "%~dp0" >nul 2>&1
if errorlevel 1 goto root_error
if not exist "scripts\judge_setup.py" goto helper_missing
where py >nul 2>&1
if errorlevel 1 goto check_python
py -3.12 -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))" >nul 2>&1
if errorlevel 1 goto check_python
py -3.12 "scripts\judge_setup.py" %*
set "ORCA_EXIT=%errorlevel%"
goto done

:check_python
where python >nul 2>&1
if errorlevel 1 goto python_missing
python -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))" >nul 2>&1
if errorlevel 1 goto python_missing
python "scripts\judge_setup.py" %*
set "ORCA_EXIT=%errorlevel%"
goto done

:python_missing
>&2 echo Python 3.12 was not found. Install the Python 3.12 Windows installer and Python Launcher,
>&2 echo open a new terminal, and check: py -3.12 --version
>&2 echo https://www.python.org/downloads/release/python-31210/
set "ORCA_EXIT=1"
goto done

:helper_missing
>&2 echo Cannot find scripts\judge_setup.py beside quickstart.bat. Restore a complete ORCA checkout.
set "ORCA_EXIT=1"
goto done

:root_error
>&2 echo Cannot enter the ORCA folder. Check that the checkout is accessible.
exit /b 1

:done
popd
exit /b %ORCA_EXIT%
