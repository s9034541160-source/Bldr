@echo off
echo Current directory: %cd%
echo Python location:
where python
echo Running Python test...
python -c "print('Hello from Python')"
echo Error level: %errorlevel%
pause