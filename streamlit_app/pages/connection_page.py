"""
飞书表格连接配置页面

提供飞书多维表格的连接配置和认证功能
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lark_tester.core.lark_client import LarkClient, LarkError
from streamlit_app.config import config_manager, LarkConfig


def test_connection(personal_token: str, app_token: str, table_id: str, domain: str) -> dict:
    """测试飞书表格连接"""
    try:
        # 创建客户端
        client = LarkClient(
            personal_token=personal_token,
            app_token=app_token,
            domain=domain
        )
        
        # 测试获取字段列表
        fields = client.list_fields(table_id)
        
        # 测试获取记录（只获取前5条）
        records = client.get_all_records(table_id, page_size=5)
        
        # 转换fields为可序列化的格式
        serializable_fields = []
        for field in fields[:10]:  # 只取前10个字段
            serializable_fields.append({
                'field_id': str(field.get('field_id', '')),
                'field_name': str(field.get('field_name', '')),
                'type': int(field.get('type', 0)),
                'description': str(field.get('description', ''))
            })
        
        return {
            'success': True,
            'message': '连接成功！',
            'fields_count': len(fields),
            'records_count': len(records),
            'fields': serializable_fields
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'连接失败: {str(e)}',
            'error': str(e)
        }


@st.cache_resource(show_spinner="创建客户端连接...")
def create_lark_client(personal_token: str, app_token: str, domain: str) -> LarkClient:
    """创建并缓存飞书客户端"""
    return LarkClient(
        personal_token=personal_token,
        app_token=app_token,
        domain=domain
    )


def render():
    """渲染连接配置页面"""
    st.header("🔗 飞书表格连接配置")
    
    # 获取当前配置（会自动从 production.yaml 加载默认配置）
    current_config = config_manager.get_lark_config()
    
    # 显示配置来源信息
    if current_config:
        default_config = config_manager.get_default_lark_config()
        if default_config and (
            current_config.personal_token == default_config.personal_token and
            current_config.app_token == default_config.app_token and
            current_config.table_id == default_config.table_id and
            current_config.domain == default_config.domain
        ):
            st.info("📄 当前使用 production.yaml 中的默认配置")
    
    # 连接状态显示
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if current_config and current_config.is_valid() and st.session_state.get('lark_client'):
            st.success("✅ 已连接到飞书表格")
        else:
            st.warning("⚠️ 未连接到飞书表格")
    
    with col2:
        if st.button("🔄 重新连接", type="secondary"):
            # 清除缓存和session state
            test_connection.clear()
            if 'lark_client' in st.session_state:
                del st.session_state['lark_client']
            st.rerun()
    
    with col3:
        if st.button("📁 加载默认配置", type="secondary"):
            # 重新加载配置文件
            config_manager._load_configs()
            default_config = config_manager.get_default_lark_config()
            if default_config:
                config_manager.save_lark_config(default_config)
                st.success("✅ 已加载默认配置")
                st.rerun()
            else:
                st.error("❌ 无法加载默认配置")
    
    st.markdown("---")
    
    # 配置表单
    with st.form("connection_form"):
        st.subheader("📝 连接参数配置")
        
        # 使用容器和列布局
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                personal_token = st.text_input(
                    "Personal Token",
                    value=current_config.personal_token if current_config else "",
                    type="password",
                    help="飞书多维表格的个人授权码，以 pt- 开头"
                )
                
                app_token = st.text_input(
                    "App Token", 
                    value=current_config.app_token if current_config else "",
                    help="应用Token，从多维表格URL中获取"
                )
            
            with col2:
                table_id = st.text_input(
                    "Table ID",
                    value=current_config.table_id if current_config else "",
                    help="表格ID，从多维表格URL中获取"
                )
                
                domain = st.text_input(
                    "API域名",
                    value=current_config.domain if current_config else "",
                    help="API域名，从 production.yaml 配置文件中读取"
                )
        
        # 保存选项
        save_to_yaml = st.checkbox(
            "💾 同时保存到 production.yaml 文件",
            value=False,
            help="勾选此项将同步更新 production.yaml 配置文件"
        )
        
        # 提交按钮
        submitted = st.form_submit_button("📊 获取表格数据", type="primary", use_container_width=True)
        
        if submitted:
            # 验证输入
            if not personal_token or not personal_token.startswith('pt-'):
                st.error("❌ Personal Token 必须以 'pt-' 开头")
                return
            
            if not app_token or not table_id:
                st.error("❌ 请填写完整的连接参数")
                return
            
            # 创建配置对象
            config = LarkConfig(
                personal_token=personal_token,
                app_token=app_token,
                table_id=table_id,
                domain=domain
            )
            
            # 保存到 session state
            config_manager.save_lark_config(config)
            
            # 保存到 YAML 文件（如果选择）
            if save_to_yaml:
                if config_manager.save_lark_config_to_yaml(config):
                    st.success("✅ 配置已保存到 production.yaml 文件")
                else:
                    st.error("❌ 保存到 YAML 文件失败")
            
            # 测试连接并获取数据
            with st.spinner("正在连接并获取表格数据..."):
                result = test_connection(personal_token, app_token, table_id, domain)
            
            if result['success']:
                # 创建并保存客户端到 session state
                st.session_state.lark_client = create_lark_client(personal_token, app_token, domain)
                
                # 显示成功信息
                st.success(f"✅ {result['message']}")
                st.rerun()
                
                # 显示表格信息
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("字段数量", result['fields_count'])
                with col2:
                    st.metric("记录数量", result['records_count'])
                
                # 显示字段信息
                if result['fields']:
                    st.subheader("📋 表格字段预览")
                    fields_data = []
                    for field in result['fields']:
                        fields_data.append({
                            '字段名': field.get('field_name', ''),
                            '字段类型': get_field_type_name(field.get('type', 0)),
                            '字段ID': field.get('field_id', '')
                        })
                    
                    st.dataframe(
                        fields_data,
                        use_container_width=True,
                        hide_index=True
                    )
                
            else:
                st.error(f"❌ {result['message']}")
                if 'error' in result:
                    with st.expander("查看详细错误信息"):
                        st.code(result['error'])
    

    
    # 配置说明
    st.markdown("---")
    with st.expander("📖 配置说明"):
        st.markdown("""
        ### 如何获取连接参数？
        
        #### 1. Personal Token (个人授权码)
        - 打开飞书多维表格
        - 点击右上角「插件」→「自定义插件」
        - 选择「获取授权码」
        - 复制生成的授权码（以 pt- 开头）
        
        #### 2. App Token 和 Table ID
        - 从多维表格的URL中获取
        - URL格式：`https://xxx.feishu.cn/base/{app_token}/tables/{table_id}`
        - 例如：`https://xxx.feishu.cn/base/UMlnbC7J4aP63AscoX9cdovCn7f/tables/tblIiquTXHImD3n6`
          - App Token: `UMlnbC7J4aP63AscoX9cdovCn7f`
          - Table ID: `tblIiquTXHImD3n6`
        
        #### 3. API域名配置
        - 统一使用飞书开放平台域名: `https://base-api.feishu.cn`
        """)


def get_field_type_name(field_type: int) -> str:
    """获取字段类型名称"""
    type_mapping = {
        1: "多行文本",
        2: "数字", 
        3: "单选",
        4: "多选",
        5: "日期",
        7: "复选框",
        11: "人员",
        13: "电话号码",
        15: "超链接",
        17: "附件",
        18: "单向关联",
        19: "查找",
        20: "公式",
        21: "双向关联",
        22: "地理位置",
        23: "群组"
    }
    return type_mapping.get(field_type, f"未知类型({field_type})")
