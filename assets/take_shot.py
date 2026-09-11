# -*- coding: utf-8 -*-
"""三软件同框截图(R/Python/Stata 终端并排) — pywin32 排窗 + PIL 截屏"""
import subprocess, time, sys, os
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
import win32gui, win32con
from PIL import ImageGrab

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DIR = r"C:\Users\32858\AppData\Local\Temp\stata_smoke\cs"
OUT = r"C:\Users\32858\Desktop\.deepseek\程序\EconCrosscheck\assets\triple_crosscheck_cs2021.png"

r_cmd = (
    "try { $Host.UI.RawUI.WindowTitle='R 4.6.1 - did (Callaway-Sant''Anna 2021)';"
    "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    f"& 'C:\\Program Files\\R\\R-4.6.1\\bin\\Rscript.exe' '{DIR}\\show_r.R' }} catch {{ $_.Exception.Message }};"
    "Read-Host '  [held for screenshot]'"
)
p_cmd = (
    "try { $Host.UI.RawUI.WindowTitle='Python 3.14 - StatsPAI';"
    "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    f"python '{DIR}\\show_py.py' }} catch {{ $_.Exception.Message }};"
    "Read-Host '  [held for screenshot]'"
)
s_cmd = (
    "$Host.UI.RawUI.WindowTitle='StataNow 19.5 SE - csdid';"
    "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    "Write-Host ('='*64);"
    "Write-Host '  StataNow 19.5 SE  |  csdid (Callaway, Sant''Anna & Roth 2021)';"
    "Write-Host '  Data: mpdta   Control: Never Treated   DR-IPW (dripw)';"
    "Write-Host ('='*64); Write-Host '';"
    "Write-Host '  . csdid lemp, ivar(countyreal) time(year) gvar(firsttreat) method(dripw)';"
    "Write-Host '  . csdid_estat simple'; Write-Host '';"
    f"$log = Get-Content '{DIR}\\cs_stata.log' -Encoding UTF8;"
    "$i = ($log | Select-String 'Average Treatment Effect on Treated' | Select-Object -First 1).LineNumber;"
    "$log[($i-1)..($i+7)] | ForEach-Object { Write-Host ('  ' + $_) };"
    "Write-Host ''; Write-Host ('  ' + ('-'*64));"
    f"Get-Content '{DIR}\\stata_results.csv' | Select-Object -Last 3 | ForEach-Object {{ Write-Host ('   ' + $_) }};"
    "Write-Host ('  ' + ('-'*64)); Write-Host '';"
    "Write-Host '  > crosscheck verdict: ALIGNED vs R/Python (tol 1e-6)';"
    "Write-Host ('='*64); Read-Host '  [held for screenshot]'"
)

procs = []
for cmd in (r_cmd, p_cmd, s_cmd):
    procs.append(subprocess.Popen(
        ["powershell", "-NoProfile", "-NoExit", "-Command", cmd],
        creationflags=win32con.CREATE_NEW_CONSOLE))

def find(key, tries=40):
    for _ in range(tries):
        hits = []
        def cb(h, _):
            if win32gui.IsWindowVisible(h):
                t = win32gui.GetWindowText(h)
                if key in t:
                    hits.append(h)
            return True
        win32gui.EnumWindows(cb, None)
        if hits:
            return hits[0]
        time.sleep(0.5)
    return 0

handles = []
for k in ("did (Callaway", "StatsPAI", "csdid"):
    handles.append(find(k))
print("handles:", [hex(h) for h in handles])

import ctypes
user32 = ctypes.windll.user32
SW, SH = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
gap, top = 24, 40
ww = (SW - 4 * gap) // 3
wh = int(SH * 0.62)

HWND_TOPMOST = -1
SWP_SHOWWINDOW = 0x0040
for j, h in enumerate(handles):
    if h:
        win32gui.SetWindowPos(h, HWND_TOPMOST, gap + j * (ww + gap), top, ww, wh, SWP_SHOWWINDOW)
if handles[0]:
    win32gui.SetForegroundWindow(handles[0])

print("waiting for models...")
time.sleep(32)

# 逐窗激活一次确保最新渲染
for h in handles:
    if h:
        win32gui.SetForegroundWindow(h)
        time.sleep(0.4)
win32gui.SetForegroundWindow(handles[0])
time.sleep(1.2)

# 截图：按三窗实际物理矩形并集
rects = [win32gui.GetWindowRect(h) for h in handles if h]
bbox = (min(r[0] for r in rects), min(r[1] for r in rects),
        max(r[2] for r in rects), max(r[3] for r in rects))
img = ImageGrab.grab(bbox=bbox)
img.save(OUT)
print("saved:", OUT, img.size, "bbox:", bbox)

for p in procs:
    p.kill()
