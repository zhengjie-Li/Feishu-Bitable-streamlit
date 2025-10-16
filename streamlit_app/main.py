"""
飞书多维表格 CRUD 操作前端

基于 Streamlit 构建的飞书多维表格管理界面
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from streamlit_app.config import init_session_state, config_manager
from streamlit_app.pages import (
    connection_page,
    data_view_page,
    field_management_page,
    analytics_page
)


def main():
    """主应用入口"""
    # 页面配置
    st.set_page_config(
        page_title="飞书多维表格管理系统",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"  # 禁用侧边栏
    )
    
    # 初始化 session state
    init_session_state()
    
    # 应用标题
    st.title("📊 飞书多维表格管理系统")
    st.markdown("---")
    
    # 页面导航
    pages = {
        "🔗 连接配置": "connection",
        "📋 数据管理": "data_view",
        "🏗️ 字段管理": "field_management",
        "📈 数据分析": "analytics"
    }
    
    # 使用 tabs 进行页面导航
    tab_names = list(pages.keys())
    tabs = st.tabs(tab_names)
    
    # 检查连接状态
    lark_config = config_manager.get_lark_config()
    is_connected = lark_config and lark_config.is_valid() and st.session_state.lark_client
    
    with tabs[0]:  # 连接配置
        connection_page.render()
    
    with tabs[1]:  # 数据查看
        if is_connected:
            data_view_page.render()
        else:
            st.warning("⚠️ 请先在「连接配置」页面配置飞书表格连接")
    
    with tabs[2]:  # 字段管理
        if is_connected:
            field_management_page.render()
        else:
            st.warning("⚠️ 请先在「连接配置」页面配置飞书表格连接")
    
    with tabs[3]:  # 数据分析
        if is_connected:
            analytics_page.render()
        else:
            st.warning("⚠️ 请先在「连接配置」页面配置飞书表格连接")
    
    # 底部信息
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            "<div style='text-align: center; color: #666;'>"
            "基于 Streamlit + FastAPI 构建的飞书多维表格管理系统"
            "</div>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()
