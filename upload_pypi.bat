@echo off
REM zimrag PyPI 发布脚本 (Windows 版本)

echo.
echo ========================================
echo   zimrag PyPI 发布脚本 (Windows)
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [1/5] 升级构建工具...
python -m pip install --upgrade build twine

echo.
echo [2/5] 清理旧构建...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist zimrag.egg-info rmdir /s /q zimrag.egg-info
if exist *.egg-info rmdir /s /q *.egg-info

echo.
echo [3/5] 构建 Python 包...
python -m build

if errorlevel 1 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo [4/5] 检查包内容...
dir dist

echo.
echo [5/5] 测试本地安装...
python -m venv test_env
call test_env\Scripts\activate
pip install dist\*.whl
python -c "import zimrag; print('zimrag v' + zimrag.__version__)"
deactivate
rmdir /s /q test_env

echo.
echo ========================================
echo   构建完成！
echo ========================================
echo.
echo 选择上传目标:
echo   1. 上传到 TestPyPI (测试)
echo   2. 上传到 PyPI (生产)
echo   3. 不上传
echo.
set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 上传到 TestPyPI...
    python -m twine upload --repository testpypi dist/*
) else if "%choice%"=="2" (
    echo.
    echo 上传到 PyPI...
    python -m twine upload dist/*
) else (
    echo.
    echo 跳过上传，包位于 dist/ 目录
)

echo.
echo 完成！
pause
