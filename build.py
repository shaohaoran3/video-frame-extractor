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
    """查找 ffmpeg 可执行文件。

    优先检测：
    0) 脚本所在目录和当前工作目录（同目录下的 ffmpeg/ffmpeg.exe 或 ffmpeg/bin/ffmpeg）
    1) 环境变量 `FFMPEG_SRC`
    2) PATH（`shutil.which`）
    3) 常见系统/包管理器路径
    4) 手动扫描 PATH 各目录
    """
    def is_executable_file(p):
        try:
            return os.path.isfile(p) and os.access(p, os.X_OK)
        except Exception:
            return False

    # 0) 优先检查脚本目录和当前工作目录
    try:
        script_dir = os.path.abspath(os.path.dirname(__file__))
    except Exception:
        script_dir = None
    try:
        cwd = os.path.abspath(os.getcwd())
    except Exception:
        cwd = None

    for base in (script_dir, cwd):
        if not base:
            continue
        # 直接可执行文件
        for name in ("ffmpeg", "ffmpeg.exe"):
            candidate = os.path.join(base, name)
            if is_executable_file(candidate):
                return os.path.abspath(candidate)
        # 常见解压结构
        candidate = os.path.join(base, "ffmpeg", "bin", "ffmpeg")
        if is_executable_file(candidate):
            return os.path.abspath(candidate)
        candidate = os.path.join(base, "ffmpeg", "bin", "ffmpeg.exe")
        if is_executable_file(candidate):
            return os.path.abspath(candidate)

    # 1) 环境变量
    env = os.environ.get("FFMPEG_SRC")
    if env:
        p = str(env).strip().strip('"').strip("'")
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            # 目录下可能直接有 ffmpeg 或 bin/ffmpeg
            candidate = os.path.join(p, "ffmpeg")
            if is_executable_file(candidate):
                return os.path.abspath(candidate)
            candidate = os.path.join(p, "bin", "ffmpeg")
            if is_executable_file(candidate):
                return os.path.abspath(candidate)
        if is_executable_file(p):
            return os.path.abspath(p)

    # 2) PATH
    which = shutil.which("ffmpeg")
    if which and is_executable_file(which):
        return os.path.abspath(which)

    # 3) 常见路径（特别是 macOS/Homebrew）
    common = [
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/usr/bin/ffmpeg",
        "/usr/local/opt/ffmpeg/bin/ffmpeg",
        "/opt/homebrew/opt/ffmpeg/bin/ffmpeg",
    ]
    for p in common:
        if is_executable_file(p):
            return os.path.abspath(p)

    # 4) 手动扫描 PATH
    path_env = os.environ.get("PATH", "")
    for d in path_env.split(os.pathsep):
        try:
            candidate = os.path.join(d, "ffmpeg")
            if is_executable_file(candidate):
                return os.path.abspath(candidate)
        except Exception:
            continue

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
    else:
        print("FFMPEG_SRC not set — build will NOT include ffmpeg (default).")

    print(f"Running PyInstaller with args: {args}")
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    main()
