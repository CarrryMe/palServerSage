@echo off
setlocal

rem 设置源目录和目标目录路径
set "source_dir=%~1"
set "target_zip=%~2"

rem 使用 PowerShell 命令将源目录打包压缩成 Zip 文件
powershell Compress-Archive -Path "%source_dir%" -DestinationPath "%target_zip%"

rem 提示操作完成
echo 操作完成。

endlocal