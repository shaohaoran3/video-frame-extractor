#!/usr/bin/env python3
"""
跨平台打包脚本 — 使用 PyInstaller 将 main.py 打包为单文件可执行程序。

此脚本只打包应用本身，不会将 ffmpeg 二进制打包进产物。
运行时会调用用户电脑中已安装的 ffmpeg。
"""

import os
import sys
import PyInstaller.__main__


def main():
    args = [
        "main.py",
        "--onefile",
        "--name=VideoFrameExtractor",
        "--clean",
    ]

    # Windows / macOS 使用 --windowed 隐藏控制台窗口
    if sys.platform in ("win32", "darwin"):
        args.append("--windowed")

    # 如果同目录下有 icon.ico（Windows）或 icon.icns（macOS），自动使用
    if sys.platform == "win32" and os.path.isfile("icon.ico"):
        args.append("--icon=icon.ico")
    elif sys.platform == "darwin" and os.path.isfile("icon.icns"):
        args.append("--icon=icon.icns")

    print("Building application without bundling ffmpeg.")
    print(f"Running PyInstaller with args: {args}")
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    main()
