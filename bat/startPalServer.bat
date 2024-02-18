@echo off

rem 检查是否提供了可执行文件路径作为命令行参数
if "%1"=="" (
    echo Usage: %0 "path\to\your\executable.exe"
    exit /b 1
)

rem 使用提供的可执行文件路径启动程序
%*
