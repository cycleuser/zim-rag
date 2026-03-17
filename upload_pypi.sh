#!/bin/bash
# zimrag PyPI 发布脚本

set -e

echo "🔧 zimrag PyPI 发布脚本"
echo "========================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo -e "\n${YELLOW}检查依赖...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误：未找到 python3${NC}"
        exit 1
    fi
    
    python3 -m pip install --upgrade build twine >/dev/null 2>&1
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
}

# 清理旧构建
clean_build() {
    echo -e "\n${YELLOW}清理旧构建文件...${NC}"
    rm -rf dist/ build/ *.egg-info
    rm -rf zimrag.egg-info/
    echo -e "${GREEN}✓ 清理完成${NC}"
}

# 构建包
build_package() {
    echo -e "\n${YELLOW}构建 Python 包...${NC}"
    python3 -m build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 构建成功${NC}"
        echo -e "\n生成的文件:"
        ls -lh dist/
    else
        echo -e "${RED}✗ 构建失败${NC}"
        exit 1
    fi
}

# 测试安装
test_install() {
    echo -e "\n${YELLOW}测试本地安装...${NC}"
    
    # 创建临时虚拟环境
    python3 -m venv /tmp/zimrag_test_venv
    source /tmp/zimrag_test_venv/bin/activate
    
    # 安装包
    pip install dist/*.whl >/dev/null 2>&1
    
    # 测试导入
    if python3 -c "import zimrag; print(f'✓ zimrag v{zimrag.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}✓ 安装测试通过${NC}"
    else
        echo -e "${RED}✗ 安装测试失败${NC}"
        deactivate
        rm -rf /tmp/zimrag_test_venv
        exit 1
    fi
    
    # 测试 CLI
    if python3 -m zimrag --version 2>/dev/null; then
        echo -e "${GREEN}✓ CLI 测试通过${NC}"
    else
        echo -e "${YELLOW}⚠ CLI 测试跳过${NC}"
    fi
    
    deactivate
    rm -rf /tmp/zimrag_test_venv
}

# 检查包内容
check_package() {
    echo -e "\n${YELLOW}检查包内容...${NC}"
    
    if [ -f dist/*.tar.gz ]; then
        echo -e "\n源码包内容:"
        tar -tzf dist/*.tar.gz | head -20
    fi
    
    if [ -f dist/*.whl ]; then
        echo -e "\nWheel 包内容:"
        unzip -l dist/*.whl | head -20
    fi
}

# 上传到 PyPI
upload_pypi() {
    echo -e "\n${YELLOW}上传到 PyPI?${NC}"
    read -p "确认上传到 PyPI (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -e "\n${YELLOW}上传到 PyPI...${NC}"
        python3 -m twine upload dist/*
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 上传成功${NC}"
            echo -e "\n查看包：https://pypi.org/project/zimrag/"
        else
            echo -e "${RED}✗ 上传失败${NC}"
            exit 1
        fi
    else
        echo -e "\n${YELLOW}跳过上传${NC}"
        echo -e "手动上传命令：python3 -m twine upload dist/*"
    fi
}

# 上传到 TestPyPI
upload_testpypi() {
    echo -e "\n${YELLOW}上传到 TestPyPI?${NC}"
    read -p "确认上传到 TestPyPI (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -e "\n${YELLOW}上传到 TestPyPI...${NC}"
        python3 -m twine upload --repository testpypi dist/*
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 上传成功${NC}"
            echo -e "\n查看包：https://test.pypi.org/project/zimrag/"
        else
            echo -e "${RED}✗ 上传失败${NC}"
            exit 1
        fi
    else
        echo -e "\n${YELLOW}跳过上传到 TestPyPI${NC}"
    fi
}

# 主函数
main() {
    echo -e "\n${GREEN}开始 PyPI 发布流程${NC}"
    
    check_dependencies
    clean_build
    build_package
    check_package
    test_install
    
    echo -e "\n${GREEN}================================${NC}"
    echo -e "${GREEN}构建和测试完成！${NC}"
    echo -e "${GREEN}================================${NC}"
    
    # 选择上传目标
    echo -e "\n${YELLOW}选择上传目标:${NC}"
    echo "1. 上传到 TestPyPI (测试)"
    echo "2. 上传到 PyPI (生产)"
    echo "3. 不上传，仅构建"
    read -p "请选择 (1/2/3): " choice
    
    case $choice in
        1)
            upload_testpypi
            ;;
        2)
            upload_pypi
            ;;
        3)
            echo -e "\n${YELLOW}包已构建完成，位于 dist/ 目录${NC}"
            ;;
        *)
            echo -e "\n${RED}无效选择${NC}"
            ;;
    esac
    
    echo -e "\n${GREEN}发布流程完成！${NC}"
}

# 运行
main "$@"
