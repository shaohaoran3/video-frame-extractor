#!/usr/bin/env python3
"""
Video Frame Extractor — 使用 FFmpeg 从视频中提取帧
支持时间点（单帧）和时间段（全部帧），输出无损图片。
"""

import os
import sys
import re
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------------------------------------------------------------------
# 隐藏 Windows 控制台窗口
# ---------------------------------------------------------------------------
_SP_KWARGS = {"creationflags": 0x08000000} if sys.platform == "win32" else {}


# ---------------------------------------------------------------------------
# FFmpeg 查找
# ---------------------------------------------------------------------------
def _is_executable_file(path):
    return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _common_ffmpeg_paths():
    name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"

    if sys.platform == "win32":
        return [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", name),
            os.path.join(os.environ.get("ProgramFiles", ""), "ffmpeg", "bin", name),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "ffmpeg", "bin", name),
            os.path.join("C:\\ffmpeg", "bin", name),
            os.path.join("C:\\ffmpeg", name),
        ]

    if sys.platform == "darwin":
        return [
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
        ]

    return [
        "/usr/local/bin/ffmpeg",
        "/usr/bin/ffmpeg",
        "/snap/bin/ffmpeg",
    ]


def _search_ffmpeg_in_path():
    name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    app_dir = os.path.normcase(os.path.abspath(_app_dir()))

    for folder in os.get_exec_path():
        if not folder:
            continue
        folder_path = os.path.normcase(os.path.abspath(folder))
        if folder_path == app_dir:
            continue
        candidate = os.path.join(folder, name)
        if _is_executable_file(candidate):
            return candidate

    return None


def find_ffmpeg():
    """只查找用户系统中已安装的 ffmpeg。"""
    for env_name in ("FFMPEG_PATH", "FFMPEG_BIN"):
        env_path = os.environ.get(env_name)
        if _is_executable_file(env_path):
            return env_path

    found = _search_ffmpeg_in_path()
    if found:
        return found

    for path in _common_ffmpeg_paths():
        if _is_executable_file(path):
            return path

    return None


# ---------------------------------------------------------------------------
# 时间解析
# ---------------------------------------------------------------------------
def parse_time(s):
    """将时间字符串解析为秒数。
    支持格式: HH:MM:SS.ms / MM:SS.ms / SS.ms / 纯秒数
    """
    s = s.strip()
    m = re.match(r"^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$", s)
    if m:
        return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    try:
        v = float(s)
    except ValueError:
        raise ValueError(f"无法解析时间: '{s}'")
    if v < 0:
        raise ValueError(f"时间不能为负数: '{s}'")
    return v


def format_time(seconds):
    """秒数 → HH:MM:SS.mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def parse_entries(text):
    """解析用户输入 → [(type, start, end), ...]
    type = 'point' | 'range'；point 时 end 为 None。
    每行一个条目，也可用逗号分隔。
    时间段用 '-' 或 '~' 分隔起止时间。
    """
    entries = []
    for line in text.strip().replace(",", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        # 尝试解析为时间段
        rm = re.match(r"^(.+?)\s*[-~]\s*(.+)$", line)
        if rm:
            try:
                start = parse_time(rm.group(1))
                end = parse_time(rm.group(2))
                if end > start:
                    entries.append(("range", start, end))
                    continue
            except ValueError:
                pass
        # 解析为单个时间点
        entries.append(("point", parse_time(line), None))
    return entries


# ---------------------------------------------------------------------------
# 打开文件夹
# ---------------------------------------------------------------------------
def open_folder(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 主界面
# ---------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("这是烧好饭给下世纪再来吃了！")
        self.root.geometry("720x620")
        self.root.minsize(640, 540)

        self.ffmpeg = find_ffmpeg()
        self.extracting = False

        self._build_ui()

        if not self.ffmpeg:
            self.log("⚠ 未找到 FFmpeg！请先在系统中安装 FFmpeg。")
            self.log("  下载地址: https://ffmpeg.org/download.html")

    # ---- 构建界面 ----
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # 视频文件
        ttk.Label(main, text="视频文件:").pack(anchor=tk.W)
        f1 = ttk.Frame(main)
        f1.pack(fill=tk.X, pady=(2, 10))
        self.video_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.video_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(f1, text="浏览...", command=self._browse_video).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # 时间输入
        ttk.Label(main, text="时间点 / 时间段（每行一个，可用逗号分隔）:").pack(anchor=tk.W)
        ttk.Label(
            main,
            text="示例:  00:01:30    1:20:00~1:25:00    90.5    30-60",
            foreground="gray",
        ).pack(anchor=tk.W)
        self.time_text = tk.Text(main, height=6, font=("Consolas", 10))
        self.time_text.pack(fill=tk.X, pady=(2, 10))

        # 输出格式
        f2 = ttk.Frame(main)
        f2.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(f2, text="输出格式:").pack(side=tk.LEFT)
        self.fmt_var = tk.StringVar(value="png")
        ttk.Combobox(
            f2,
            textvariable=self.fmt_var,
            values=["png", "bmp", "tiff"],
            state="readonly",
            width=8,
        ).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(
            f2, text="(PNG=无损压缩  BMP/TIFF=完全无压缩)", foreground="gray"
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 输出目录
        ttk.Label(main, text="输出目录:").pack(anchor=tk.W)
        f3 = ttk.Frame(main)
        f3.pack(fill=tk.X, pady=(2, 10))
        self.out_var = tk.StringVar()
        ttk.Entry(f3, textvariable=self.out_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(f3, text="浏览...", command=self._browse_output).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # 按钮
        bf = ttk.Frame(main)
        bf.pack(pady=(0, 10))
        self.extract_btn = ttk.Button(bf, text="  提取帧  ", command=self._start)
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        self.open_btn = ttk.Button(
            bf, text="打开输出目录", command=self._open_output, state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 5))

        # 日志
        ttk.Label(main, text="日志:").pack(anchor=tk.W)
        lf = ttk.Frame(main)
        lf.pack(fill=tk.BOTH, expand=True)
        self.log_box = tk.Text(lf, height=8, state=tk.DISABLED, font=("Consolas", 9))
        sb = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # ---- 日志输出 ----
    def log(self, msg):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    # ---- 文件/目录选择 ----
    def _browse_video(self):
        p = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[
                (
                    "视频文件",
                    "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.ts *.mts *.mpg *.mpeg",
                ),
                ("所有文件", "*.*"),
            ],
        )
        if p:
            self.video_var.set(p)
            if not self.out_var.get():
                self.out_var.set(
                    os.path.join(os.path.dirname(p), "extracted_frames")
                )

    def _browse_output(self):
        p = filedialog.askdirectory(title="选择输出目录")
        if p:
            self.out_var.set(p)

    def _open_output(self):
        d = self.out_var.get().strip()
        if d and os.path.isdir(d):
            open_folder(d)

    # ---- 启动提取 ----
    def _start(self):
        if self.extracting:
            return

        if not self.ffmpeg:
            messagebox.showerror(
                "错误", "未找到 FFmpeg！\n请先在系统中安装 FFmpeg，并确保命令 ffmpeg 可用。"
            )
            return

        video = self.video_var.get().strip()
        if not video or not os.path.isfile(video):
            messagebox.showerror("错误", "请选择一个有效的视频文件。")
            return

        raw = self.time_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showerror("错误", "请输入至少一个时间点或时间段。")
            return

        try:
            entries = parse_entries(raw)
        except ValueError as e:
            messagebox.showerror("解析错误", str(e))
            return
        if not entries:
            messagebox.showerror("错误", "未找到有效的时间条目。")
            return

        out_dir = self.out_var.get().strip()
        if not out_dir:
            messagebox.showerror("错误", "请选择输出目录。")
            return

        os.makedirs(out_dir, exist_ok=True)

        self.extracting = True
        self.extract_btn.configure(state=tk.DISABLED)
        self.open_btn.configure(state=tk.DISABLED)
        self.progress["value"] = 0

        threading.Thread(
            target=self._run,
            args=(video, entries, out_dir, self.fmt_var.get()),
            daemon=True,
        ).start()

    # ---- 后台提取 ----
    def _run(self, video, entries, out_dir, fmt):
        try:
            name = os.path.splitext(os.path.basename(video))[0]
            # 清理文件名中的特殊字符
            name = re.sub(r'[<>:"/\\|?*]', "_", name)
            total = len(entries)
            self.root.after(0, self.log, f"开始提取: {os.path.basename(video)}")

            for i, (etype, start, end) in enumerate(entries, 1):
                if etype == "point":
                    self._extract_point(name, video, start, out_dir, fmt, i, total)
                else:
                    self._extract_range(name, video, start, end, out_dir, fmt, i, total)

                self.root.after(0, self._set_progress, i / total * 100)

            self.root.after(0, self.log, f"全部完成！输出目录: {out_dir}")
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "完成", f"帧提取完成！\n\n保存位置:\n{out_dir}"
                ),
            )
        except Exception as e:
            self.root.after(0, self.log, f"错误: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
        finally:
            self.root.after(0, self._done)

    def _extract_point(self, name, video, t, out_dir, fmt, idx, total):
        ts = format_time(t)
        safe = ts.replace(":", "-").replace(".", "_")
        out = os.path.join(out_dir, f"{name}_{safe}.{fmt}")

        self.root.after(0, self.log, f"[{idx}/{total}] 提取 {ts} 处的帧...")

        cmd = [self.ffmpeg, "-ss", ts, "-i", video, "-frames:v", "1", "-y", out]
        r = subprocess.run(cmd, capture_output=True, text=True, **_SP_KWARGS)

        if r.returncode == 0 and os.path.isfile(out):
            size_kb = os.path.getsize(out) / 1024
            self.root.after(
                0, self.log, f"  ✓ {os.path.basename(out)}  ({size_kb:.1f} KB)"
            )
        else:
            err = (r.stderr or "")[-300:]
            self.root.after(0, self.log, f"  ✗ 失败: {err}")

    def _extract_range(self, name, video, start, end, out_dir, fmt, idx, total):
        ss = format_time(start)
        es = format_time(end)
        safe_s = ss.replace(":", "-").replace(".", "_")
        safe_e = es.replace(":", "-").replace(".", "_")
        rdir = os.path.join(out_dir, f"{name}_{safe_s}_to_{safe_e}")
        os.makedirs(rdir, exist_ok=True)

        self.root.after(0, self.log, f"[{idx}/{total}] 提取 {ss} ~ {es} 的所有帧...")

        dur = end - start
        cmd = [
            self.ffmpeg,
            "-ss", ss,
            "-i", video,
            "-t", f"{dur:.3f}",
            "-vsync", "0",
            "-y",
            os.path.join(rdir, f"frame_%06d.{fmt}"),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, **_SP_KWARGS)

        if r.returncode == 0:
            count = len([f for f in os.listdir(rdir) if f.endswith(f".{fmt}")])
            self.root.after(
                0,
                self.log,
                f"  ✓ 共提取 {count} 帧 → {os.path.basename(rdir)}/",
            )
        else:
            err = (r.stderr or "")[-300:]
            self.root.after(0, self.log, f"  ✗ 失败: {err}")

    def _set_progress(self, val):
        self.progress["value"] = val

    def _done(self):
        self.extracting = False
        self.extract_btn.configure(state=tk.NORMAL)
        self.open_btn.configure(state=tk.NORMAL)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main():
    # Windows DPI 感知（需在创建 Tk 前调用）
    if sys.platform == "win32":
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
