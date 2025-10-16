# Feishu-Bitable-streamlit

> 基于飞书(Lark)多维表格的接口解决方案

🎯 项目简介

基于 Streamlit 构建的飞书多维表格 CRUD 操作前端界面，提供直观易用的数据管理和分析功能。

- 📊 **可视化数据管理**: 通过现代化 Web 界面管理飞书表格数据
- 🔧 **字段动态管理**: 在线创建、编辑、删除表格字段，无需编程
- 📈 **实时数据分析**: 内置数据分析和可视化图表功能
- 🚀 **零配置启动**: 一键启动 Web 界面，开箱即用

### ✨ 核心特性

- 🔥 **零学习成本**: 在熟悉的多维表格中管理测试用例
- 🚀 **现代化架构**: 基于原始baseopensdk重构，支持最新Python版本
- 🔐 **简化认证**: 只需personal_token，无需复杂应用配置
- 📊 **实时回写**: 测试结果自动回写到表格，形成完整数据闭环
- 🔧 **字段管理**: 完整的字段CRUD操作，支持动态表格改造
- 🖥️ **Web 可视化界面**: 基于 Streamlit 的现代化前端，支持数据管理、字段操作和实时分析

## 🎉 精简表格设计

经过深度优化，框架采用**精简优先**的设计理念，将字段从31个精简至13个核心字段：

### 🎯 核心测试字段 (11个)

| 字段名     | 类型     | 说明                   | 示例                                       |
| ---------- | -------- | ---------------------- | ------------------------------------------ |
| 接口编号   | 自动编号 | 【系统生成】唯一标识符 | 1, 2, 3...                                 |
| 接口名称   | 文本     | 【必填】功能描述       | 用户登录接口                               |
| 接口路径   | 文本     | 【必填】API路径        | /api/auth/login                            |
| 请求方法   | 单选     | 【必填】HTTP方法       | POST                                       |
| 请求头     | 多行文本 | 【可选】JSON格式       | {"Content-Type": "application/json"}       |
| 请求体     | 多行文本 | 【可选】JSON格式       | {"username": "test", "password": "123456"} |
| 预期状态码 | 数字     | 【必填】期望状态码     | 200                                        |
| 响应状态码 | 文本     | 【系统填写】实际状态码 | 200                                        |
| 响应体     | 多行文本 | 【系统填写】响应数据   | {"code": "00000", "data": {...}}           |
| 断言规则   | 多行文本 | 【可选】验证规则       | {"status_code": "== 200"}                  |
| 是否通过   | 单选     | 【系统填写】测试结果   | 通过/失败                                  |

## 🚀 快速开始

### 📋 环境要求

- **Python**: 3.8+
- **飞书账号**: 具备多维表格访问权限
- **网络**: 能访问 `https://base-api.feishu.cn`

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 
pip install -r requirements.txt
```

### 2. 启动应用

```bash
# 方式1: 使用启动脚本（推荐）
python run_streamlit.py
```

### 3. 访问应用

打开浏览器访问: http://localhost:8501

### 🔐 参数获取

#### 获取授权码

1. 打开你的飞书多维表格
2. 点击右上角 **「插件」**→ **「自定义插件」**
3. 选择 **「获取授权码」**
4. 复制生成的 `personal_token`（以 `pt-`开头）

#### URL提取配置信息

多维表格URL格式：

```
https://domain.feishu.cn/base/APP_TOKEN?table=TABLE_ID&view=VIEW_ID
```

- `APP_TOKEN`: 位于 `/base/` 和 `?table=` 之间
- `TABLE_ID`: 位于 `?table=` 和 `&view=` 之间

## 🏗️ 项目架构

```
Lark-operation/
├── lark_tester/                 # 核心框架
│   ├── core/                   # 核心模块
│   │   ├── lark_client.py      # Lark API客户端（基于原始SDK重构）
│   │   ├── test_executor.py    # 测试执行引擎
│   │   ├── config_manager.py   # 配置管理器
│   │   └── result_manager.py   # 结果回写管理器
│   ├── utils/                  # 工具模块
│   │   ├── logger.py          # 日志工具
│   │   └── validator.py       # 数据验证器
│   └── cli.py                 # 命令行接口
├── streamlit_app/              # Streamlit Web 前端
│   ├── main.py                # 主应用入口
│   ├── config.py              # 前端配置管理
│   └── pages/                 # 页面模块
│       ├── connection_page.py      # 连接配置页面
│       ├── data_view_page.py      # 数据查看管理页面
│       ├── field_management_page.py # 字段管理页面
│       └── analytics_page.py      # 数据分析页面
├── config/                     # 配置文件
│   ├── production.yaml        # 生产环境配置
│   └── development.yaml       # 开发环境配置
├── run_streamlit.py           # Streamlit 启动脚本
├── examples/                  # 示例代码
└── field_usage_guide.md       # 字段使用指南
```

## 🔧 核心技术特性

### 💪 现代化SDK重构

- **完全兼容**: 保持与原始baseopensdk的认证逻辑一致
- **现代化实现**: 使用requests库替代过时依赖
- **字段管理**: 支持字段的创建、删除、更新、查询操作
- **类型安全**: 严格的字段类型验证和转换

### 🎯 精简设计理念

基于**渐进式功能扩展**原则：

1. **简洁优先**: 13个核心字段满足80%的测试需求
2. **按需扩展**: 复杂功能通过代码层面实现
3. **用户友好**: 新手可快速上手，专家有扩展空间
4. **维护简单**: 字段少、逻辑清晰、文档完整

### 🚀 字段管理API

基于原始baseopensdk的字段管理功能：

```python
from lark_tester.core.lark_client import LarkClient

client = LarkClient(personal_token="pt-xxx", app_token="xxx")

# 创建字段
field = client.create_field(
    table_id="tbl123",
    field_name="新字段",
    field_type=1,  # 多行文本
    description="字段描述"
)

# 列出所有字段
fields = client.list_fields("tbl123")

# 更新字段
client.update_field("tbl123", "fld456", field_name="更新后的字段名")

# 删除字段
client.delete_field("tbl123", "fld456")
```

## 📖 详细文档

- **[字段使用指南](field_usage_guide.md)** - 详细的字段说明和最佳实践
- **[Streamlit 前端文档](README_STREAMLIT.md)** - Web 前端功能详细说明

## 🖥️ Streamlit Web 前端功能

### 📋 功能概览

| 功能模块               | 描述               | 主要特性                               |
| ---------------------- | ------------------ | -------------------------------------- |
| 🔗**连接配置**   | 飞书 API 认证配置  | 可视化配置、连接测试、状态检测         |
| 📊**数据管理**   | 表格数据 CRUD 操作 | 数据查看、编辑、删除、批量导入导出     |
| 🏗️**字段管理** | 动态字段操作       | 创建、修改、删除字段，支持多种字段类型 |
| 📈**数据分析**   | 数据可视化分析     | 统计图表、趋势分析、数据洞察           |

### 代码规范

- **PEP 8**: Python代码风格标准
- **类型提示**: 使用type hints提高代码可读性
- **文档字符串**: 所有公共方法都要有docstring
- **单元测试**: 核心功能必须有测试覆盖

## 🐛 故障排除

### 常见问题

#### 1. 认证失败

```
错误: invalid access token (20005)
解决: 
- 检查personal_token是否正确
- 确认token未过期
- 验证表格访问权限
```

#### 2. 字段不匹配

```
错误: FieldNameNotFound
解决:
- 确保表格字段名与框架要求完全一致
- 检查字段是否已创建
- 使用validate命令验证表格结构
```

#### 3. 网络连接问题

```
错误: Connection timeout
解决:
- 检查网络连接
- 确认API域名配置正确
- 尝试使用代理
```

## 📈 性能与限制

### API限制

- **请求频率**: 建议不超过10次/秒
- **数据量**: 单次最多200条记录
- **字段数量**: 建议不超过50个字段
- **Token有效期**: 通常90天，需定期更新

### 性能优化

- **批量操作**: 使用批量API减少请求次数
- **缓存机制**: 字段信息本地缓存
- **异步执行**: 大量用例可考虑并发执行
- **分页处理**: 大数据集自动分页加载

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

如果这个项目对您有帮助，请给一个 ⭐ Star 以表示支持！您的支持是我们持续改进的动力。
