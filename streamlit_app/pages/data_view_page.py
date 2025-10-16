"""
表格数据管理页面

提供数据查看、编辑、删除、批量上传功能
"""

import streamlit as st
import pandas as pd
import sys
import io
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lark_tester.core.lark_client import LarkClient
from streamlit_app.config import config_manager


@st.cache_data(ttl=300, show_spinner="加载表格数据...")
def load_table_data(client_hash: str, table_id: str, page_size: int = 100) -> Dict[str, Any]:
    """加载表格数据"""
    try:
        client = st.session_state.lark_client
        if not client:
            return {'success': False, 'message': '客户端未初始化'}
        
        # 获取字段信息
        fields = client.list_fields(table_id)
        
        # 获取记录数据
        records = client.get_all_records(table_id, page_size=page_size)
        
        return {
            'success': True,
            'fields': fields,
            'records': records,
            'total_count': len(records)
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'加载数据失败: {str(e)}'
        }


def format_field_value(value: Any, field_type: int) -> str:
    """格式化字段值用于显示"""
    if value is None or value == '':
        return ''
    
    # 根据字段类型格式化显示
    if field_type == 2:  # 数字
        try:
            return str(float(value))
        except (ValueError, TypeError):
            return str(value)
    elif field_type == 5:  # 日期
        if isinstance(value, (int, float)):
            # 时间戳转换
            try:
                dt = datetime.fromtimestamp(value / 1000)
                return dt.strftime('%Y-%m-%d')
            except (ValueError, OSError):
                return str(value)
        return str(value)
    elif field_type == 1001:  # 日期时间
        if isinstance(value, (int, float)):
            # 时间戳转换
            try:
                dt = datetime.fromtimestamp(value / 1000)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, OSError):
                return str(value)
        return str(value)
    elif field_type == 3:  # 单选
        if isinstance(value, dict):
            return value.get('text', str(value))
        return str(value)
    elif field_type == 4:  # 多选
        if isinstance(value, list):
            return ', '.join([item.get('text', str(item)) if isinstance(item, dict) else str(item) for item in value])
        return str(value)
    else:
        return str(value)


def process_field_value(value: Any, field_type: int) -> Any:
    """处理字段值用于API提交"""
    if value is None or value == '':
        return None
    
    # 根据字段类型处理值
    if field_type == 2:  # 数字
        try:
            # 尝试转换为数字
            if isinstance(value, str):
                # 移除可能的千分位分隔符
                cleaned_value = value.replace(',', '').replace(' ', '')
                if '.' in cleaned_value:
                    return float(cleaned_value)
                else:
                    return int(cleaned_value)
            return float(value)
        except (ValueError, TypeError):
            return str(value)  # 如果转换失败，保持原值
    elif field_type == 5:  # 日期
        if isinstance(value, str):
            try:
                # 尝试解析日期字符串
                dt = datetime.strptime(value, '%Y-%m-%d')
                return int(dt.timestamp() * 1000)  # 转换为毫秒时间戳
            except ValueError:
                try:
                    # 尝试其他日期格式
                    dt = datetime.strptime(value, '%Y/%m/%d')
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    return str(value)  # 如果解析失败，保持原值
        return value
    elif field_type == 1001:  # 日期时间
        if isinstance(value, str):
            try:
                # 尝试解析日期时间字符串
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                return int(dt.timestamp() * 1000)  # 转换为毫秒时间戳
            except ValueError:
                try:
                    # 尝试其他格式
                    dt = datetime.strptime(value, '%Y/%m/%d %H:%M:%S')
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    return str(value)  # 如果解析失败，保持原值
        return value
    else:
        # 其他类型保持原值
        return str(value)


def create_dataframe_from_records(records: List[Dict], fields: List[Dict]) -> pd.DataFrame:
    """将记录转换为 DataFrame"""
    if not records:
        return pd.DataFrame()
    
    # 创建字段映射
    field_map = {field['field_id']: field for field in fields}
    
    # 转换数据
    data_rows = []
    for record in records:
        row = {'记录ID': record['record_id']}
        
        for field_id, value in record['fields'].items():
            field_info = field_map.get(field_id, {})
            field_name = field_info.get('field_name', field_id)
            field_type = field_info.get('type', 1)
            
            # 格式化值
            formatted_value = format_field_value(value, field_type)
            row[field_name] = formatted_value
        
        data_rows.append(row)
    
    return pd.DataFrame(data_rows)


def generate_template(fields: List[Dict]) -> bytes:
    """生成Excel模板文件"""
    # 创建模板数据
    template_data = {}
    field_descriptions = {}
    
    for field in fields:
        field_name = field['field_name']
        field_type = field['type']
        
        # 跳过系统字段
        if field_name in ['记录ID', 'record_id'] or field_type in [19, 20, 1001, 1002, 1003, 1004]:
            continue
        
        template_data[field_name] = [""]  # 空值作为示例
        
        # 添加字段描述
        if field_type == 1:  # 多行文本
            field_descriptions[field_name] = "文本类型"
        elif field_type == 2:  # 数字
            field_descriptions[field_name] = "数字类型"
        elif field_type == 3:  # 单选
            field_descriptions[field_name] = "单选类型"
        elif field_type == 4:  # 多选
            field_descriptions[field_name] = "多选类型，多个值用逗号分隔"
        elif field_type == 5:  # 日期
            field_descriptions[field_name] = "日期类型，格式：YYYY-MM-DD"
        elif field_type == 7:  # 复选框
            field_descriptions[field_name] = "复选框类型，填写：是/否"
        elif field_type == 11:  # 人员
            field_descriptions[field_name] = "人员类型，填写用户ID或邮箱"
        elif field_type == 13:  # 电话号码
            field_descriptions[field_name] = "电话号码类型"
        elif field_type == 15:  # 超链接
            field_descriptions[field_name] = "超链接类型，格式：显示文本|链接地址"
        else:
            field_descriptions[field_name] = f"字段类型: {field_type}"
    
    # 创建DataFrame
    df = pd.DataFrame(template_data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 写入数据
        df.to_excel(writer, sheet_name='数据模板', index=False)
        
        # 写入字段说明
        desc_df = pd.DataFrame([
            {'字段名': k, '说明': v} for k, v in field_descriptions.items()
        ])
        desc_df.to_excel(writer, sheet_name='字段说明', index=False)
    
    return output.getvalue()


def parse_uploaded_file(uploaded_file) -> Optional[pd.DataFrame]:
    """解析上传的文件"""
    try:
        if uploaded_file.name.endswith('.csv'):
            # 尝试不同的编码
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    return df
                except UnicodeDecodeError:
                    continue
            return None
        else:
            # Excel文件
            df = pd.read_excel(uploaded_file, sheet_name=0)
            return df
    except Exception as e:
        st.error(f"文件解析错误: {str(e)}")
        return None


def validate_upload_data(df: pd.DataFrame, fields: List[Dict]) -> Dict[str, Any]:
    """验证上传的数据"""
    errors = []
    
    # 获取可用字段名
    available_fields = [f['field_name'] for f in fields if f['field_name'] not in ['记录ID', 'record_id']]
    
    # 检查列名
    df_columns = df.columns.tolist()
    invalid_columns = [col for col in df_columns if col not in available_fields]
    
    if invalid_columns:
        errors.append(f"无效的列名: {', '.join(invalid_columns)}")
    
    # 检查是否有有效数据
    valid_columns = [col for col in df_columns if col in available_fields]
    if not valid_columns:
        errors.append("没有找到有效的字段列")
    
    # 检查空行
    empty_rows = df.isnull().all(axis=1).sum()
    if empty_rows > 0:
        errors.append(f"发现 {empty_rows} 行空数据")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'valid_columns': valid_columns
    }


def create_batch_records(client: LarkClient, table_id: str, df: pd.DataFrame, fields: List[Dict]):
    """批量创建记录"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    error_count = 0
    error_details = []
    
    total_records = len(df)
    
    # 获取字段映射 - 使用field_id作为键，确保准确匹配
    field_name_to_info = {field.get('field_name', ''): field for field in fields}
    field_id_map = {field.get('field_id', ''): field for field in fields}
    
    # 调试信息：显示字段映射
    with st.expander("🔍 调试信息 - 字段映射详情", expanded=False):
        st.write("**可用字段映射:**")
        for field_name, field_info in field_name_to_info.items():
            st.write(f"  - 字段名: `{field_name}` → 字段ID: `{field_info.get('field_id', 'N/A')}`")
        
        st.write("**上传数据的列名:**")
        for col in df.columns:
            st.write(f"  - 列名: `{col}`")
            if col in field_name_to_info:
                st.success(f"    ✅ 匹配成功")
            else:
                st.error(f"    ❌ 未找到匹配的字段")
    
    # 验证字段映射
    unmapped_columns = [col for col in df.columns if col not in field_name_to_info]
    if unmapped_columns:
        st.error(f"❌ 以下列名在飞书表格中未找到对应字段: {', '.join(unmapped_columns)}")
        st.info("💡 请确保上传文件的列名与飞书表格中的字段名完全一致（包括大小写和空格）")
        return
    
    for idx, row in df.iterrows():
        try:
            # 更新进度
            progress = (idx + 1) / total_records
            progress_bar.progress(progress)
            status_text.text(f"正在创建第 {idx + 1}/{total_records} 条记录...")
            
            # 构建记录数据 - 使用字段名称作为键
            record_data = {}
            
            for col, value in row.items():
                # 跳过空值
                if value == '' or pd.isna(value):
                    continue
                    
                # 获取字段信息
                field_info = field_name_to_info.get(col)
                if field_info:
                    # 根据字段类型处理值
                    field_type = field_info.get('type', 1)
                    processed_value = process_field_value(value, field_type)
                    # 使用字段名称而不是field_id作为键
                    record_data[col] = processed_value
            
            # 创建记录
            if record_data:  # 只有当有数据时才创建
                result = client.create_record(table_id, record_data)
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    error_details.append(f"第 {idx + 2} 行：创建失败")
            else:
                error_count += 1
                error_details.append(f"第 {idx + 2} 行：无有效数据")
                
        except Exception as e:
            error_count += 1
            error_details.append(f"第 {idx + 2} 行：{str(e)}")
    
    # 完成进度
    progress_bar.progress(1.0)
    status_text.text("批量创建完成！")
    
    # 显示结果
    st.markdown("---")
    st.markdown("### 📊 批量创建结果")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ 成功创建", success_count)
    with col2:
        st.metric("❌ 创建失败", error_count)
    with col3:
        st.metric("📊 总计", total_records)
    
    if error_details:
        with st.expander("❌ 错误详情", expanded=False):
            for error in error_details[:20]:  # 最多显示20个错误
                st.error(error)
            if len(error_details) > 20:
                st.info(f"还有 {len(error_details) - 20} 个错误未显示")
    
    if success_count > 0:
        st.success(f"🎉 批量创建完成！成功创建了 {success_count} 条记录")
        
        # 清除缓存以刷新数据
        load_table_data.clear()


def render_batch_upload(client: LarkClient, table_id: str, fields: List[Dict]):
    """渲染批量上传界面"""
    st.subheader("📤 批量上传记录")
    
    # 创建两列布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📋 模板下载")
        st.info("💡 请先下载模板文件，按照模板格式填写数据后上传")
        
        # 生成模板按钮
        if st.button("📥 下载Excel模板", type="primary"):
            template_data = generate_template(fields)
            st.download_button(
                label="💾 点击下载模板文件",
                data=template_data,
                file_name=f"lark_table_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        st.markdown("### 📤 文件上传")
        uploaded_file = st.file_uploader(
            "选择要上传的文件",
            type=['xlsx', 'xls', 'csv'],
            help="支持 Excel (.xlsx, .xls) 和 CSV (.csv) 格式"
        )
    
    if uploaded_file is not None:
        st.markdown("---")
        st.markdown("### 📊 数据预览与验证")
        
        try:
            # 解析上传的文件
            df = parse_uploaded_file(uploaded_file)
            
            if df is not None and not df.empty:
                st.success(f"✅ 成功读取文件，共 {len(df)} 行数据")
                
                # 数据预览
                with st.expander("👀 数据预览", expanded=True):
                    st.dataframe(
                        df.head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                    if len(df) > 10:
                        st.info(f"仅显示前10行，总共{len(df)}行数据")
                
                # 数据验证
                validation_result = validate_upload_data(df, fields)
                
                if validation_result['is_valid']:
                    st.success("✅ 数据格式验证通过")
                    
                    # 显示将要创建的记录数量
                    st.info(f"📝 准备创建 {len(df)} 条记录")
                    
                    # 批量创建按钮
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        if st.button("🚀 开始批量创建", type="primary", use_container_width=True):
                            create_batch_records(client, table_id, df, fields)
                else:
                    st.error("❌ 数据验证失败")
                    for error in validation_result['errors']:
                        st.error(f"• {error}")
                    
                    st.warning("⚠️ 请修正数据后重新上传")
            else:
                st.error("❌ 文件为空或格式不正确")
                
        except Exception as e:
            st.error(f"❌ 文件解析失败: {str(e)}")


def handle_record_update(client: LarkClient, table_id: str, record_id: str, field_name: str, new_value: Any):
    """处理记录更新"""
    try:
        # 构建更新数据 - 使用字段名称而不是field_id
        update_data = {field_name: new_value}
        
        # 调用API更新记录
        success = client.update_record(table_id, record_id, update_data)
        
        if success:
            st.success(f"✅ 记录 {record_id} 更新成功")
            # 清除缓存以刷新数据
            load_table_data.clear()
            return True
        else:
            st.error(f"❌ 记录 {record_id} 更新失败")
            return False
            
    except Exception as e:
        st.error(f"❌ 更新记录时发生错误: {str(e)}")
        return False


def handle_record_delete(client: LarkClient, table_id: str, record_id: str):
    """处理记录删除"""
    try:
        success = client.delete_record(table_id, record_id)
        
        if success:
            st.success(f"✅ 记录 {record_id} 删除成功")
            # 清除缓存以刷新数据
            load_table_data.clear()
            return True
        else:
            st.error(f"❌ 记录 {record_id} 删除失败")
            return False
            
    except Exception as e:
        st.error(f"❌ 删除记录时发生错误: {str(e)}")
        return False


def render():
    """渲染数据管理页面"""
    st.header("📋 表格数据管理")
    
    # 检查连接状态
    config = config_manager.get_lark_config()
    
    if not st.session_state.lark_client or not config:
        st.warning("⚠️ 请先在「连接配置」页面配置飞书表格连接")
        
        # 提供快速跳转按钮
        if st.button("🔗 前往连接配置", type="primary"):
            st.switch_page("pages/connection_page.py")
        return
    
    client = st.session_state.lark_client
    
    # 功能选择
    tab1, tab2 = st.tabs(["📊 数据查看与编辑", "📤 批量上传"])
    
    with tab1:
        # 控制面板
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.info(f"📊 当前表格: {config.table_id}")
        
        with col2:
            page_size = st.selectbox(
                "每页显示",
                options=[50, 100, 200, 500],
                index=1,
                help="选择每页显示的记录数量"
            )
        
        with col3:
            if st.button("🔄 刷新数据", type="secondary"):
                # 清除缓存
                load_table_data.clear()
                st.rerun()
        
        # 自动加载数据
        st.info("🔄 正在自动加载表格数据...")
        client_hash = str(hash(str(client)))  # 用于缓存键
        data_result = load_table_data(client_hash, config.table_id, page_size)
        
        if not data_result['success']:
            st.error(f"❌ {data_result['message']}")
            return
        
        fields = data_result['fields']
        records = data_result['records']
        total_count = data_result['total_count']
        
        # 数据统计
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总记录数", total_count)
        with col2:
            st.metric("字段数量", len(fields))
        with col3:
            st.metric("已加载", len(records))
        
        st.markdown("---")
        
        # 搜索和筛选
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_text = st.text_input(
                    "🔍 搜索记录",
                    placeholder="输入关键词搜索记录内容...",
                    help="在所有字段中搜索包含关键词的记录"
                )
            
            with col2:
                field_filter = st.selectbox(
                    "筛选字段",
                    options=["全部字段"] + [f['field_name'] for f in fields],
                    help="选择要显示的字段"
                )
        
        # 转换为 DataFrame
        df = create_dataframe_from_records(records, fields)
        
        if df.empty:
            st.warning("📭 暂无数据")
            return
        
        # 应用搜索筛选
        filtered_df = df.copy()
        
        if search_text:
            # 在所有列中搜索
            mask = filtered_df.astype(str).apply(
                lambda x: x.str.contains(search_text, case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[mask]
        
        # 应用字段筛选
        if field_filter != "全部字段":
            display_columns = ['记录ID', field_filter]
            filtered_df = filtered_df[display_columns]
        
        # 显示筛选结果统计
        if len(filtered_df) != len(df):
            st.info(f"🔍 筛选结果: {len(filtered_df)} / {len(df)} 条记录")
        
        # 可编辑数据表格
        st.subheader("📊 可编辑数据表格")
        st.info("💡 双击单元格可直接编辑，修改后点击「保存更改」按钮同步到飞书")
        
        # 配置列显示
        column_config = {}
        for field in fields:
            field_name = field['field_name']
            field_type = field['type']
            
            if field_name == '记录ID':
                column_config[field_name] = st.column_config.TextColumn(
                    field_name,
                    disabled=True,  # 记录ID不可编辑
                    help="记录的唯一标识符，不可编辑"
                )
            elif field_type == 2:  # 数字类型
                column_config[field_name] = st.column_config.NumberColumn(
                    field_name,
                    format="%.2f"
                )
            elif field_type == 5:  # 日期类型
                column_config[field_name] = st.column_config.DatetimeColumn(
                    field_name,
                    format="YYYY-MM-DD HH:mm:ss"
                )
            elif field_type == 7:  # 复选框
                column_config[field_name] = st.column_config.CheckboxColumn(field_name)
            elif field_type == 15:  # 超链接
                column_config[field_name] = st.column_config.LinkColumn(field_name)
        
        # 使用 data_editor 显示可编辑表格
        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            height=400,
            key="editable_table"
        )
        
        # 检测数据变化并提供保存按钮
        if not edited_df.equals(filtered_df):
            st.warning("⚠️ 检测到数据变化，请点击「保存更改」按钮同步到飞书")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 保存更改", type="primary"):
                    # 处理数据更新
                    changes_made = 0
                    
                    # 创建字段映射
                    field_name_to_id = {field['field_name']: field['field_id'] for field in fields}
                    
                    # 调试信息：显示字段映射
                    with st.expander("🔍 调试信息 - 编辑字段映射", expanded=False):
                        st.write("**可用字段映射:**")
                        for field_name, field_id in field_name_to_id.items():
                            st.write(f"  - 字段名: `{field_name}` → 字段ID: `{field_id}`")
                        
                        st.write("**DataFrame列名:**")
                        for col in filtered_df.columns:
                            st.write(f"  - 列名: `{col}`")
                            if col in field_name_to_id:
                                st.success(f"    ✅ 匹配成功")
                            else:
                                st.error(f"    ❌ 未找到匹配的字段")
                    
                    # 比较原始数据和编辑后的数据
                    for idx in range(len(filtered_df)):
                        # 安全地获取记录ID（第一列）
                        record_id = edited_df.iloc[idx, 0]  # 记录ID是第一列
                        
                        # 检查每个字段的变化
                        for col_name in filtered_df.columns:
                            if col_name == '记录ID':
                                continue
                                
                            original_value = filtered_df.iloc[idx][col_name]
                            edited_value = edited_df.iloc[idx][col_name]
                            
                            if str(original_value) != str(edited_value):
                                field_id = field_name_to_id.get(col_name)
                                if field_id:
                                    # 获取字段类型信息
                                    field_info = next((f for f in fields if f.get('field_name') == col_name), {})
                                    field_type = field_info.get('type', 1)
                                    
                                    # 处理字段值
                                    processed_value = process_field_value(edited_value, field_type)
                                    
                                    with st.expander(f"🔄 更新字段: {col_name}", expanded=False):
                                        st.write(f"**字段名:** {col_name}")
                                        st.write(f"**原始值:** {original_value}")
                                        st.write(f"**新值:** {edited_value}")
                                        st.write(f"**处理后值:** {processed_value}")
                                    
                                    # 使用字段名称而不是field_id进行更新
                                    success = handle_record_update(client, config.table_id, record_id, col_name, processed_value)
                                    if success:
                                        changes_made += 1
                                else:
                                    st.warning(f"⚠️ 字段 '{col_name}' 在字段映射中未找到，无法更新")
                    
                    if changes_made > 0:
                        st.success(f"✅ 成功更新了 {changes_made} 个字段")
                        st.rerun()
                    else:
                        st.info("ℹ️ 没有检测到有效的更改")
            
            with col2:
                if st.button("❌ 取消更改", type="secondary"):
                    st.rerun()
        
        # 批量删除功能
        st.markdown("---")
        st.subheader("🗑️ 批量删除记录")
        st.warning("⚠️ 删除操作不可逆，请谨慎操作！")
        
        # 选择要删除的记录
        if not filtered_df.empty:
            selected_records = st.multiselect(
                "选择要删除的记录",
                options=filtered_df['记录ID'].tolist(),
                help="可以选择多个记录进行批量删除"
            )
            
            if selected_records:
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("🗑️ 确认删除", type="primary"):
                        deleted_count = 0
                        for record_id in selected_records:
                            success = handle_record_delete(client, config.table_id, record_id)
                            if success:
                                deleted_count += 1
                        
                        if deleted_count > 0:
                            st.success(f"✅ 成功删除了 {deleted_count} 条记录")
                            st.rerun()
                        else:
                            st.error("❌ 删除操作失败")
        
        # 数据导出
        st.markdown("---")
        st.subheader("📥 数据导出")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📥 导出 CSV", type="secondary"):
                csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载 CSV 文件",
                    data=csv_data,
                    file_name=f"lark_table_data_{config.table_id}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 复制数据", type="secondary"):
                # 将数据复制到剪贴板（显示为文本）
                text_data = filtered_df.to_string(index=False)
                st.text_area("复制以下内容:", text_data, height=100)
        
        # 字段信息面板
        with st.expander("📋 字段信息"):
            field_info_data = []
            for field in fields:
                field_info_data.append({
                    '字段名': field['field_name'],
                    '字段类型': get_field_type_name(field['type']),
                    '字段ID': field['field_id'],
                    '描述': field.get('description', {}).get('text', '') or '无'
                })
            
            st.dataframe(
                field_info_data,
                use_container_width=True,
                hide_index=True
            )
    
    with tab2:
        # 批量上传功能
        render_batch_upload(client, config.table_id, fields)


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
