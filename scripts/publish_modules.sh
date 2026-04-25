#!/usr/bin/env bash
# 造价 Agent 模块化发布脚本
# 用法: bash publish.sh [module_name]
# 模块名: all | matcher | calculator | quota | knowledge | tracking | change_order | api | web

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$SCRIPT_DIR/.."
PUBLISH_DIR="/tmp/cost-agent-publish"
VERSION="6.0.0"

echo "=== 造价 Agent v${VERSION} 模块化发布 ==="
echo ""

MODULE="${1:-all}"

publish_module() {
    local name="$1"
    local src="$2"
    local dest="$PUBLISH_DIR/$name"
    
    echo "发布模块: $name"
    mkdir -p "$dest"
    
    # 复制文件
    if [ -d "$src" ]; then
        cp -r "$src"/* "$dest/" 2>/dev/null || true
    elif [ -f "$src" ]; then
        cp "$src" "$dest/"
    fi
    
    # 复制 SKILL.md（如果存在）
    if [ -f "$src/SKILL.md" ]; then
        cp "$src/SKILL.md" "$dest/SKILL.md"
    fi
    
    echo "  → $dest"
}

# 清理
rm -rf "$PUBLISH_DIR"
mkdir -p "$PUBLISH_DIR"

case "$MODULE" in
    all)
        echo "发布所有模块..."
        publish_module "knowledge" "$AGENT_DIR/knowledge"
        publish_module "calculators" "$AGENT_DIR/calculators"
        publish_module "data/quotas" "$AGENT_DIR/data/quotas"
        publish_module "cost_tracking" "$AGENT_DIR/cost_tracking"
        publish_module "change_order" "$AGENT_DIR/change_order"
        publish_module "core" "$AGENT_DIR/core"
        publish_module "api" "$AGENT_DIR/api"
        publish_module "web" "$AGENT_DIR/web"
        ;;
    matcher|knowledge)
        publish_module "knowledge" "$AGENT_DIR/knowledge"
        ;;
    calculator|calculators)
        publish_module "calculators" "$AGENT_DIR/calculators"
        ;;
    quota|data)
        publish_module "data/quotas" "$AGENT_DIR/data/quotas"
        ;;
    tracking|cost_tracking)
        publish_module "cost_tracking" "$AGENT_DIR/cost_tracking"
        ;;
    change_order|change)
        publish_module "change_order" "$AGENT_DIR/change_order"
        ;;
    core)
        publish_module "core" "$AGENT_DIR/core"
        ;;
    api)
        publish_module "api" "$AGENT_DIR/api"
        ;;
    web)
        publish_module "web" "$AGENT_DIR/web"
        ;;
    *)
        echo "未知模块: $MODULE"
        echo "可用模块: all | matcher | calculator | quota | knowledge | tracking | change_order | api | web | core"
        exit 1
        ;;
esac

# 生成发布清单
cat > "$PUBLISH_DIR/PUBLISH.md" << EOF
# 造价 Agent v${VERSION} 发布

> 发布时间: $(date '+%Y-%m-%d %H:%M:%S')
> 发布模块: ${MODULE}
> 作者: 太一 AGI

## 发布内容

$(cd "$PUBLISH_DIR" && find . -type f -name "*.py" -o -name "*.md" -o -name "*.json" | head -50)

## 使用

参考各模块的 SKILL.md 获取使用说明。
EOF

echo ""
echo "✅ 发布完成: $PUBLISH_DIR"
echo ""
ls -la "$PUBLISH_DIR"
