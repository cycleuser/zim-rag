# zimrag PyPI 发布指南

## 准备工作

### 1. 安装构建工具

```bash
pip install --upgrade build twine
```

### 2. 配置 PyPI 凭证

创建 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
```

## 发布流程

### 方法一：自动脚本（推荐）

**Linux/macOS:**
```bash
cd zimrag
./upload_pypi.sh
```

**Windows:**
```cmd
cd zimrag
upload_pypi.bat
```

### 方法二：手动步骤

```bash
# 1. 清理旧构建
rm -rf dist/ build/ *.egg-info

# 2. 构建包
python -m build

# 3. 测试本地安装
pip install dist/*.whl

# 4. 测试导入
python -c "import zimrag; print(zimrag.__version__)"

# 5. 上传到 TestPyPI（测试）
python -m twine upload --repository testpypi dist/*

# 6. 测试 TestPyPI 安装
pip install --index-url https://test.pypi.org/simple/ zimrag

# 7. 上传到 PyPI（生产）
python -m twine upload dist/*
```

## 验证安装

```bash
# 创建干净环境
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 安装
pip install zimrag

# 验证
zim-rag --version
python -m zimrag --version

# 测试导入
python -c "from zimrag import ZIMRAGAPI; print('OK')"
```

## 版本管理

### 更新版本号

编辑 `pyproject.toml`:

```toml
[project]
version = "1.0.1"  # 更新版本号
```

### 版本命名规范

- `1.0.0` - 主版本.次版本.修订版本
- `1.0.0a1` - Alpha 测试版
- `1.0.0b1` - Beta 测试版
- `1.0.0rc1` - Release Candidate

## 常见问题

### 1. 上传失败：403 Forbidden

**原因**: 凭证错误或包名已存在

**解决**:
- 检查 `~/.pypirc` 配置
- 确认使用 API Token 而非密码
- 包名在 PyPI 上唯一

### 2. 构建失败：ModuleNotFoundError

**原因**: 缺少构建依赖

**解决**:
```bash
pip install --upgrade build twine setuptools
```

### 3. 安装后 CLI 不可用

**原因**: entry_points 配置错误

**检查** `pyproject.toml`:
```toml
[project.scripts]
zim-rag = "zimrag.interfaces.cli:main"
```

### 4. 包内容不完整

**原因**: MANIFEST.in 配置问题

**解决**: 编辑 `MANIFEST.in` 添加缺失文件

## PyPI 链接

- **TestPyPI**: https://test.pypi.org/project/zimrag/
- **PyPI**: https://pypi.org/project/zimrag/

## 发布检查清单

- [ ] 更新版本号
- [ ] 更新 CHANGELOG.md
- [ ] 运行测试套件
- [ ] 构建包
- [ ] 测试本地安装
- [ ] 上传到 TestPyPI
- [ ] 测试 TestPyPI 安装
- [ ] 上传到 PyPI
- [ ] 验证 PyPI 页面
- [ ] 创建 Git 标签
- [ ] 发布 GitHub Release

## 安全提示

- ⚠️ **不要**将 PyPI token 提交到代码库
- ⚠️ 使用环境变量存储敏感信息
- ⚠️ 定期轮换 API token
- ⚠️ 启用双因素认证 (2FA)

## 资源链接

- [PyPI 官方文档](https://packaging.python.org/)
- [twine 文档](https://twine.readthedocs.io/)
- [build 文档](https://pypa-build.readthedocs.io/)
