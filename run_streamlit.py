#!/usr/bin/env python3
"""
飞书多维表格 Streamlit 前端启动脚本

使用方法:
    python run_streamlit.py
    
或者直接运行:
    streamlit run streamlit_app/main.py
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """启动 Streamlit 应用"""
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    # Streamlit 应用主文件路径
    app_file = project_root / "streamlit_app" / "main.py"
    
    if not app_file.exists():
        print(f"❌ 错误: 找不到应用文件 {app_file}")
        sys.exit(1)
    
    # 检查依赖
    try:
        import streamlit
        print("✅ Streamlit 已安装")
    except ImportError:
        print("❌ 错误: 未安装 Streamlit")
        print("请运行: pip install -r streamlit_requirements.txt")
        sys.exit(1)
    
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)
    
    # 启动命令
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_file),
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("🚀 启动飞书多维表格 Streamlit 前端...")
    print(f"📂 项目目录: {project_root}")
    print(f"📄 应用文件: {app_file}")
    print(f"🌐 访问地址: http://localhost:8501")
    print("=" * 50)
    
    try:
        # 启动 Streamlit
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
