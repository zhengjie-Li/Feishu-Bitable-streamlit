"""
字段管理页面

提供字段的创建、修改、删除功能
"""

import streamlit as st
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lark_tester.core.lark_client import LarkClient
from streamlit_app.config import config_manager


# 字段类型映射
FIELD_TYPE_MAP = {
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
    19: "查找引用",
    20: "公式",
    21: "双向关联",
    22: "地理位置",
    23: "群组",
    1001: "创建时间",
    1002: "最后更新时间",
    1003: "创建人",
    1004: "修改人"
}

# 可创建的字段类型
CREATABLE_FIELD_TYPES = {
    1: "多行文本",
    2: "数字", 
    3: "单选",
    4: "多选",
    5: "日期",
    7: "复选框",
    13: "电话号码",
    15: "超链接"
}


def render():
    """渲染字段管理页面"""
    st.header("🔧 字段管理")
    
    # 检查连接状态
    if not st.session_state.lark_client:
        st.error("❌ 请先在连接配置页面建立连接")
        return
    
    client = st.session_state.lark_client
    config = config_manager.get_lark_config()
    
    if not config:
        st.error("❌ 配置信息丢失，请重新配置连接")
        return
    
    # 操作选择
    operation = st.radio(
        "选择操作",
        options=["查看字段", "创建字段", "修改字段", "删除字段"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if operation == "查看字段":
        render_view_fields(client, config.table_id)
    elif operation == "创建字段":
        render_create_field(client, config.table_id)
    elif operation == "修改字段":
        render_modify_field(client, config.table_id)
    elif operation == "删除字段":
        render_delete_field(client, config.table_id)


def render_view_fields(client: LarkClient, table_id: str):
    """渲染查看字段界面"""
    st.subheader("👁️ 查看表格字段")
    
    try:
        with st.spinner("正在加载字段信息..."):
            fields = client.list_fields(table_id)
        
        if not fields:
            st.warning("⚠️ 未找到任何字段")
            return
        
        st.success(f"✅ 共找到 {len(fields)} 个字段")
        
        # 字段统计
        col1, col2, col3 = st.columns(3)
        
        field_type_count = {}
        for field in fields:
            field_type = field.get('type', 0)
            type_name = FIELD_TYPE_MAP.get(field_type, f"未知类型({field_type})")
            field_type_count[type_name] = field_type_count.get(type_name, 0) + 1
        
        with col1:
            st.metric("字段总数", len(fields))
        with col2:
            st.metric("字段类型数", len(field_type_count))
        with col3:
            most_common_type = max(field_type_count.items(), key=lambda x: x[1])
            st.metric("最常用类型", f"{most_common_type[0]} ({most_common_type[1]})")
        
        # 字段列表
        st.subheader("📋 字段详情")
        
        # 搜索和过滤
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 搜索字段名称", placeholder="输入字段名称进行搜索")
        with col2:
            filter_type = st.selectbox(
                "筛选字段类型",
                options=["全部"] + list(set(FIELD_TYPE_MAP.get(f.get('type', 0), f"未知类型({f.get('type', 0)})") for f in fields))
            )
        
        # 过滤字段
        filtered_fields = fields
        if search_term:
            filtered_fields = [f for f in filtered_fields if search_term.lower() in f['field_name'].lower()]
        if filter_type != "全部":
            filtered_fields = [f for f in filtered_fields if FIELD_TYPE_MAP.get(f.get('type', 0), f"未知类型({f.get('type', 0)})") == filter_type]
        
        # 显示字段
        for i, field in enumerate(filtered_fields):
            with st.expander(f"🏷️ {field['field_name']} ({FIELD_TYPE_MAP.get(field.get('type', 0), f'未知类型({field.get('type', 0)})')})", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**基本信息:**")
                    st.write(f"- **字段ID:** `{field['field_id']}`")
                    st.write(f"- **字段名称:** {field['field_name']}")
                    st.write(f"- **字段类型:** {FIELD_TYPE_MAP.get(field.get('type', 0), f'未知类型({field.get('type', 0)})')}")
                    st.write(f"- **类型代码:** {field.get('type', 0)}")
                
                with col2:
                    st.write("**完整配置:**")
                    st.json(field, expanded=False)
                
                # 显示字段属性
                if 'property' in field and field['property']:
                    st.write("**字段属性:**")
                    property_data = field['property']
                    
                    # 单选/多选选项
                    if 'options' in property_data:
                        st.write("选项列表:")
                        for opt in property_data['options']:
                            st.write(f"  - {opt.get('name', '未命名')} (ID: {opt.get('id', 'N/A')})")
                    
                    # 其他属性
                    other_props = {k: v for k, v in property_data.items() if k != 'options'}
                    if other_props:
                        st.json(other_props, expanded=False)
        
        if not filtered_fields:
            st.info("🔍 没有找到匹配的字段")
            
    except Exception as e:
        st.error(f"❌ 获取字段信息失败: {str(e)}")


def render_create_field(client: LarkClient, table_id: str):
    """渲染创建字段界面"""
    st.subheader("➕ 创建新字段")
    
    with st.form("create_field_form"):
        # 基本信息
        field_name = st.text_input(
            "字段名称 *",
            placeholder="输入字段名称",
            help="字段名称不能为空"
        )
        
        field_type = st.selectbox(
            "字段类型 *",
            options=list(CREATABLE_FIELD_TYPES.keys()),
            format_func=lambda x: f"{CREATABLE_FIELD_TYPES[x]} ({x})",
            help="选择字段类型"
        )
        
        # 根据字段类型显示额外配置
        field_property = {}
        
        if field_type in [3, 4]:  # 单选或多选
            st.subheader("选项配置")
            st.write("为单选/多选字段添加选项:")
            
            # 动态添加选项
            if 'field_options' not in st.session_state:
                st.session_state.field_options = ["选项1"]
            
            options = []
            for i, option in enumerate(st.session_state.field_options):
                col1, col2 = st.columns([4, 1])
                with col1:
                    option_name = st.text_input(f"选项 {i+1}", value=option, key=f"option_{i}")
                    if option_name.strip():
                        options.append({"name": option_name.strip()})
                with col2:
                    if st.button("❌", key=f"remove_{i}", help="删除此选项"):
                        st.session_state.field_options.pop(i)
                        st.rerun()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ 添加选项"):
                    st.session_state.field_options.append(f"选项{len(st.session_state.field_options)+1}")
                    st.rerun()
            
            if options:
                field_property["options"] = options
        
        elif field_type == 2:  # 数字
            st.subheader("数字字段配置")
            col1, col2 = st.columns(2)
            with col1:
                precision = st.number_input("小数位数", min_value=0, max_value=10, value=0)
            with col2:
                formatter = st.selectbox("数字格式", options=["0", "0.0", "0.00", "0%", "0.0%"])
            
            field_property.update({
                "precision": precision,
                "formatter": formatter
            })
        
        elif field_type == 15:  # 超链接
            st.subheader("超链接字段配置")
            st.info("超链接字段将存储URL和显示文本")
        
        # 提交按钮
        submitted = st.form_submit_button("✅ 创建字段", type="primary", use_container_width=True)
        
        if submitted:
            if not field_name.strip():
                st.error("❌ 字段名称不能为空")
                return
            
            try:
                # 构建字段配置
                field_config = {
                    "field_name": field_name.strip(),
                    "type": field_type
                }
                
                if field_property:
                    field_config["property"] = field_property
                
                with st.spinner("正在创建字段..."):
                    result = client.create_field(table_id, field_config)
                
                if result:
                    st.success(f"✅ 字段创建成功！字段ID: {result.get('field_id', 'N/A')}")
                    
                    # 显示创建的字段信息
                    with st.expander("查看创建的字段"):
                        st.json(result)
                    
                    # 清除选项状态
                    if 'field_options' in st.session_state:
                        del st.session_state.field_options
                    
                    # 提供重新创建选项
                    if st.button("🔄 创建另一个字段"):
                        st.rerun()
                else:
                    st.error("❌ 字段创建失败")
                    
            except Exception as e:
                st.error(f"❌ 创建字段时发生错误: {str(e)}")


def render_modify_field(client: LarkClient, table_id: str):
    """渲染修改字段界面"""
    st.subheader("📝 修改字段")
    
    # 获取字段列表
    try:
        fields = client.list_fields(table_id)
        if not fields:
            st.warning("⚠️ 未找到任何字段")
            return
    except Exception as e:
        st.error(f"❌ 获取字段列表失败: {str(e)}")
        return
    
    # 字段选择
    field_options = {f"{field['field_name']} ({field['field_id']})": field for field in fields}
    selected_field_key = st.selectbox(
        "选择要修改的字段",
        options=list(field_options.keys()),
        help="选择一个字段进行修改"
    )
    
    if not selected_field_key:
        return
    
    selected_field = field_options[selected_field_key]
    field_type = selected_field.get('type', 0)
    
    st.info(f"📋 当前字段类型: {FIELD_TYPE_MAP.get(field_type, f'未知类型({field_type})')}")
    
    # 显示当前字段信息
    with st.expander("查看当前字段配置", expanded=False):
        st.json(selected_field)
    
    # 修改表单
    with st.form("modify_field_form"):
        # 字段名称修改
        new_field_name = st.text_input(
            "字段名称",
            value=selected_field['field_name'],
            help="修改字段名称"
        )
        
        # 根据字段类型显示可修改的属性
        field_property = selected_field.get('property', {}).copy()
        
        if field_type in [3, 4]:  # 单选或多选
            st.subheader("选项管理")
            
            current_options = field_property.get('options', [])
            
            # 显示现有选项
            st.write("**现有选项:**")
            updated_options = []
            
            for i, option in enumerate(current_options):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    option_name = st.text_input(
                        f"选项 {i+1}",
                        value=option.get('name', ''),
                        key=f"modify_option_{i}"
                    )
                with col2:
                    keep_option = st.checkbox("保留", value=True, key=f"keep_option_{i}")
                with col3:
                    st.write(f"ID: {option.get('id', 'N/A')}")
                
                if keep_option and option_name.strip():
                    updated_options.append({
                        "name": option_name.strip(),
                        "id": option.get('id')
                    })
            
            # 添加新选项
            st.write("**添加新选项:**")
            new_option_name = st.text_input("新选项名称", key="new_option_modify")
            if new_option_name.strip():
                updated_options.append({"name": new_option_name.strip()})
            
            field_property["options"] = updated_options
        
        elif field_type == 2:  # 数字
            st.subheader("数字格式配置")
            current_precision = field_property.get('precision', 0)
            current_formatter = field_property.get('formatter', '0')
            
            col1, col2 = st.columns(2)
            with col1:
                precision = st.number_input("小数位数", min_value=0, max_value=10, value=current_precision)
            with col2:
                formatter = st.selectbox(
                    "数字格式", 
                    options=["0", "0.0", "0.00", "0%", "0.0%"],
                    index=["0", "0.0", "0.00", "0%", "0.0%"].index(current_formatter) if current_formatter in ["0", "0.0", "0.00", "0%", "0.0%"] else 0
                )
            
            field_property.update({
                "precision": precision,
                "formatter": formatter
            })
        
        # 提交按钮
        submitted = st.form_submit_button("💾 保存修改", type="primary", use_container_width=True)
        
        if submitted:
            if not new_field_name.strip():
                st.error("❌ 字段名称不能为空")
                return
            
            try:
                # 构建更新配置
                update_config = {
                    "field_name": new_field_name.strip()
                }
                
                if field_property:
                    update_config["property"] = field_property
                
                with st.spinner("正在更新字段..."):
                    success = client.update_field(table_id, selected_field['field_id'], update_config)
                
                if success:
                    st.success("✅ 字段更新成功！")
                    st.rerun()
                else:
                    st.error("❌ 字段更新失败")
                    
            except Exception as e:
                st.error(f"❌ 更新字段时发生错误: {str(e)}")


def render_delete_field(client: LarkClient, table_id: str):
    """渲染删除字段界面"""
    st.subheader("🗑️ 删除字段")
    
    st.error("⚠️ 删除字段将永久删除该字段及其所有数据，此操作不可逆！")
    
    # 获取字段列表
    try:
        fields = client.list_fields(table_id)
        if not fields:
            st.warning("⚠️ 未找到任何字段")
            return
    except Exception as e:
        st.error(f"❌ 获取字段列表失败: {str(e)}")
        return
    
    # 过滤掉系统字段
    deletable_fields = [f for f in fields if f.get('type', 0) not in [1001, 1002, 1003, 1004]]
    
    if not deletable_fields:
        st.warning("⚠️ 没有可删除的字段（系统字段不能删除）")
        return
    
    # 字段选择
    field_options = {f"{field['field_name']} ({FIELD_TYPE_MAP.get(field.get('type', 0), f'未知类型({field.get('type', 0)})')})": field for field in deletable_fields}
    selected_field_key = st.selectbox(
        "选择要删除的字段",
        options=[""] + list(field_options.keys()),
        help="选择一个字段进行删除"
    )
    
    if not selected_field_key:
        return
    
    selected_field = field_options[selected_field_key]
    
    # 显示字段信息
    st.markdown("---")
    st.subheader("📋 字段信息预览")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**字段名称:** {selected_field['field_name']}")
        st.write(f"**字段ID:** `{selected_field['field_id']}`")
        st.write(f"**字段类型:** {FIELD_TYPE_MAP.get(selected_field.get('type', 0), f'未知类型({selected_field.get('type', 0)})')}")
    
    with col2:
        with st.expander("查看完整字段配置"):
            st.json(selected_field)
    
    # 删除确认
    st.markdown("---")
    st.error("🚨 确认删除此字段？")
    
    # 二次确认
    confirm_text = st.text_input(
        "请输入字段名称以确认删除",
        placeholder=f"输入 '{selected_field['field_name']}' 确认删除",
        help="为防止误删，请输入完整的字段名称"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🗑️ 确认删除", type="primary", disabled=(confirm_text != selected_field['field_name'])):
            try:
                with st.spinner("正在删除字段..."):
                    success = client.delete_field(table_id, selected_field['field_id'])
                
                if success:
                    st.success("✅ 字段删除成功！")
                    st.rerun()
                else:
                    st.error("❌ 字段删除失败")
                    
            except Exception as e:
                st.error(f"❌ 删除字段时发生错误: {str(e)}")
    
    with col2:
        if st.button("❌ 取消删除", type="secondary"):
            st.rerun()
    
    if confirm_text != selected_field['field_name'] and confirm_text:
        st.warning("⚠️ 输入的字段名称不匹配，请检查后重试")
