#!/bin/bash

# 检查是否提供了可执行文件路径作为命令行参数
if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/your/executable"
    exit 1
fi

# 使用提供的可执行文件路径启动程序
nohup sh "$@" > nohup.out 2>&1 &
