#!/usr/bin/env python3
"""
跨平台打包脚本 — 使用 PyInstaller 将 main.py 打包为单文件可执行程序。

此脚本会在发现本地 ffmpeg（二进制）时将其一并打包，方便用户无需额外安装 ffmpeg。

可通过环境变量 `FFMPEG_SRC` 指定要打包的 ffmpeg 路径。
"""

import os
import sys
import shutil
import PyInstaller.__main__


def find_local_ffmpeg():
    """查找 ffmpeg 可执行文件，优先使用环境变量 FFMPEG_SRC。"""
    env = os.environ.get("FFMPEG_SRC")
    if env:
        if os.path.isfile(env):
            return env
    candidates = [
        "ffmpeg",
        "ffmpeg.exe",
        os.path.join("ffmpeg", "bin", "ffmpeg"),
        os.path.join("ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # 最后尝试 PATH
    which = shutil.which("ffmpeg")
    if which:
        return which
    return None


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

    # 如果能找到 ffmpeg 可执行文件，则把它打包进可执行文件（放到运行目录）
    ff = find_local_ffmpeg()
    if ff:
        ff_abspath = os.path.abspath(ff)
        # PyInstaller 的 --add-binary 格式: Windows 使用 ';'，POSIX 使用 ':'
        sep = ";" if sys.platform == "win32" else ":"
        args.append(f"--add-binary={ff_abspath}{sep}.")
        print(f"Including ffmpeg binary: {ff_abspath}")

    print(f"Running PyInstaller with args: {args}")
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    main()
