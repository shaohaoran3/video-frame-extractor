# Video Frame Extractor

使用 FFmpeg 从视频中提取帧的桌面工具。支持按时间点提取单帧或按时间段提取所有帧，输出无损图片。

## 功能

- **时间点提取** — 输入一个时间，导出该时刻的一帧图片
- **时间段提取** — 输入起止时间，导出该区间内所有帧
- **批量操作** — 支持同时输入多个时间点 / 时间段
- **无损输出** — 支持 PNG（无损压缩）、BMP、TIFF（完全无压缩）
- **跨平台** — Windows、macOS、Linux

## 前置依赖

- **FFmpeg** — 必须预先安装在用户电脑上，并确保系统可以找到 `ffmpeg`
  - Windows: https://www.gyan.dev/ffmpeg/builds/ （下载 release full → 解压 → 将 bin 目录加入 PATH）
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg` 或 `sudo dnf install ffmpeg`

## 直接运行（开发模式）

需要 Python 3.8+（tkinter 已内置，无需额外安装）：

```bash
python main.py
```

## 打包为单文件可执行程序

```bash
# 1. 安装打包依赖
pip install -r requirements.txt

# 2. 执行打包
python build.py
```

打包完成后，可执行文件在 `dist/` 目录中：

| 平台    | 产物                                |
| ------- | ----------------------------------- |
| Windows | `dist/VideoFrameExtractor.exe`      |
| macOS   | `dist/VideoFrameExtractor.app`      |
| Linux   | `dist/VideoFrameExtractor`          |

将可执行文件分发给用户后，程序会直接调用用户电脑里已安装的 FFmpeg；打包产物本身不包含 FFmpeg。

## 打包说明与跨平台构建

- 原因：PyInstaller 在宿主机上构建本机二进制，不能在 Windows 上直接交叉构建 macOS 或 Linux 程序。

- 本地构建（在目标平台上运行）：
  - Windows：`python build.py`
  - Linux：在 Linux 主机或 WSL/容器 中运行 `python build.py`
  - macOS：在 macOS 主机上运行 `python build.py`

- 自动 CI 构建（推荐）：仓库中已附带 GitHub Actions workflow（`.github/workflows/build.yml`），它会在 `windows-latest` / `ubuntu-latest` / `macos-latest` 上构建并将可执行产物作为 artifact 上传。

- 运行方式：程序本质上是一个图形化的 FFmpeg 命令执行器，打包后的应用不会携带 FFmpeg，而是调用用户系统里已安装的 FFmpeg。

## 时间格式说明

| 格式              | 示例                  | 含义                    |
| ----------------- | --------------------- | ----------------------- |
| `HH:MM:SS`        | `01:23:45`            | 1小时23分45秒处的帧     |
| `HH:MM:SS.mmm`    | `00:02:30.500`        | 2分30秒500毫秒处的帧    |
| `MM:SS`            | `5:30`                | 5分30秒处的帧           |
| 纯秒数            | `90.5`                | 第90.5秒处的帧          |
| 时间段 (`-` / `~`) | `01:00:00-01:05:00`   | 1小时到1小时5分的所有帧 |

每行写一个条目，也可以用逗号分隔多个条目。

## 许可证

MIT
