#!/bin/bash
echo "🔁 正在重启 ComfyUI ..."
supervisorctl restart comfyui
echo "📄 日志输出 (Ctrl+C 停止查看)："
tail -f /var/log/comfyui.out.log
