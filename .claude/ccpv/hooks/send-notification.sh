#!/usr/bin/env bash
# Stop Hook: 跨平台系统通知
set -euo pipefail

TITLE="${1:-Claude Code}"
MESSAGE="${2:-当前任务已处理完成}"

# 转义特殊字符，防止命令注入
escape_for_osascript() {
    # 转义双引号和反斜杠
    printf '%s' "${1//\\/\\\\}" | sed 's/"/\\"/g'
}

notify_linux() {
    if command -v notify-send &>/dev/null; then
        notify-send "$TITLE" "$MESSAGE" --icon=dialog-information --expire-time=5000
    elif command -v zenity &>/dev/null; then
        zenity --notification --text="$TITLE: $MESSAGE" 2>/dev/null || true
    else
        echo "[WARN] 未找到 notify-send 或 zenity，跳过系统通知" >&2
    fi
}

notify_macos() {
    local escaped_title escaped_message
    escaped_title=$(escape_for_osascript "$TITLE")
    escaped_message=$(escape_for_osascript "$MESSAGE")
    osascript -e "display notification \"$escaped_message\" with title \"$escaped_title\""
}

notify_windows() {
    # 构造 PowerShell 命令
    local ps_script
    ps_script="
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
\$notification = New-Object System.Windows.Forms.NotifyIcon
\$notification.Icon = [System.Drawing.SystemIcons]::Information
\$notification.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
\$notification.BalloonTipTitle = '$TITLE'
\$notification.BalloonTipText = '$MESSAGE'
\$notification.Visible = \$true
\$notification.ShowBalloonTip(5000)
Start-Sleep -Seconds 6
\$notification.Dispose()
"
    powershell.exe -ExecutionPolicy Bypass -Command "$ps_script" 2>/dev/null || \
    powershell.exe -ExecutionPolicy Bypass -Command "$ps_script" 2>/dev/null || {
        echo "[WARN] 无法调用 PowerShell，跳过系统通知" >&2
    }
}

case "$(uname -s)" in
    Linux*)   notify_linux ;;
    Darwin*)  notify_macos ;;
    MINGW*|MSYS*|CYGWIN*)  notify_windows ;;
    *)
        # 兜底：尝试检测是否在 Windows 环境
        if command -v powershell.exe &>/dev/null; then
            notify_windows
        else
            echo "[WARN] 未知操作系统: $(uname -s)，跳过系统通知" >&2
        fi
        ;;
esac