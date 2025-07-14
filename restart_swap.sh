#!/bin/bash
echo "🔁 正在重启 AI-Swap 接口 ..."
supervisorctl restart ai-swap
echo "📄 日志输出 (Ctrl+C 停止查看)："
tail -f /var/log/ai-swap.out.log


# supervisorctl stop ai-swap
# supervisorctl stop comfyui

# supervisorctl start ai-swap
# supervisorctl start comfyui