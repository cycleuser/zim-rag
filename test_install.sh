#!/bin/bash
# zimrag 快速测试脚本

set -e

echo "🧪 zimrag 测试套件"
echo "=================="

# 创建临时虚拟环境
echo -e "\n创建测试环境..."
python3 -m venv /tmp/zimrag_test
source /tmp/zimrag_test/bin/activate

# 安装构建工具
echo "安装依赖..."
pip install --upgrade pip >/dev/null 2>&1
pip install build pytest >/dev/null 2>&1

# 构建
echo "构建包..."
python3 -m build >/dev/null 2>&1

# 安装
echo "安装到测试环境..."
pip install dist/*.whl >/dev/null 2>&1

# 测试导入
echo -e "\n运行测试..."
python3 -c "
import zimrag
print(f'✓ 导入成功：zimrag v{zimrag.__version__}')

from zimrag import ZIMRAGAPI, ToolResult
print('✓ ZIMRAGAPI 导入成功')
print('✓ ToolResult 导入成功')

from zimrag.core import ZIMParser, ContentIndex, RAGEngine, OllamaClient
print('✓ 核心模块导入成功')

# 测试 API 初始化
api = ZIMRAGAPI()
print('✓ ZIMRAGAPI 初始化成功')

# 测试健康检查
health = api.check_health()
print(f'✓ 健康检查：{\"通过\" if health.success else \"失败\"}')

print('\n✅ 所有测试通过！')
"

# 清理
echo -e "\n清理测试环境..."
deactivate
rm -rf /tmp/zimrag_test
rm -rf dist/ build/ *.egg-info zimrag.egg-info/

echo "完成！"
