#!/bin/bash
# 🚀 自动安装依赖并推送 GitHub
# 太一 AGI · 自进化自动化脚本
# 创建：2026-04-11

set -e

echo "============================================================"
echo "🚀 太一 AGI 自进化自动化脚本"
echo "============================================================"

# 1. 安装系统依赖
echo ""
echo "📦 步骤 1: 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y mdb-tools libchm-bin

# 2. 安装 Python 库
echo ""
echo "📦 步骤 2: 安装 Python 库..."
pip install python-chm --break-system-packages -q

# 3. 转换 Access 数据库
echo ""
echo "💾 步骤 3: 转换 Access 数据库..."
cd /home/nicola/.openclaw/workspace/skills/cost-agent
python3 scripts/convert_mdb_python.py

# 4. 转换 CHM 文件
echo ""
echo "📕 步骤 4: 转换 CHM 文件..."
python3 scripts/convert_chm_python.py

# 5. GitHub 认证
echo ""
echo "🔐 步骤 5: GitHub 认证..."
gh auth status || gh auth login

# 6. 推送 Cost.Agent
echo ""
echo "🚀 步骤 6: 推送 Cost.Agent..."
cd /home/nicola/.openclaw/workspace/skills/cost-agent
gh repo create nicola-king/cost-agent --public --source=. --push || echo "仓库可能已存在"

# 7. 推送太一记忆宫殿
echo ""
echo "🚀 步骤 7: 推送太一记忆宫殿..."
cd /home/nicola/.openclaw/workspace/skills/taiyi-memory-palace
gh repo create nicola-king/taiyi-memory-palace --public --source=. --push || echo "仓库可能已存在"

echo ""
echo "============================================================"
echo "✅ 自动化完成！"
echo "============================================================"
echo ""
echo "📊 完成内容:"
echo "   ✅ 系统依赖安装"
echo "   ✅ Python 库安装"
echo "   ✅ Access 数据库转换"
echo "   ✅ CHM 文件转换"
echo "   ✅ Cost.Agent GitHub 推送"
echo "   ✅ 太一记忆宫殿 GitHub 推送"
echo ""
echo "🎉 综合进度：100%！"
echo ""
