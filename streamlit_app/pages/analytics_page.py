"""
数据分析和可视化页面

提供表格数据的统计分析和可视化功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lark_tester.core.lark_client import LarkClient
from streamlit_app.config import config_manager


@st.cache_data(ttl=3600, show_spinner="加载数据...")
def load_table_data(_client: LarkClient, table_id: str) -> Optional[pd.DataFrame]:
    """加载表格数据并转换为DataFrame"""
    try:
        records = _client.get_all_records(table_id)
        if not records:
            return None
        
        # 获取字段信息
        fields = _client.list_fields(table_id)
        field_map = {field['field_id']: field['field_name'] for field in fields}
        
        # 转换为DataFrame
        data_rows = []
        for record in records:
            row = {'record_id': record['record_id']}
            for field_id, value in record['fields'].items():
                field_name = field_map.get(field_id, field_id)
                
                # 处理不同类型的字段值
                if isinstance(value, dict):
                    if 'text' in value:  # 单选等
                        row[field_name] = value['text']
                    elif 'link' in value:  # 超链接
                        row[field_name] = value.get('text', value['link'])
                    else:
                        row[field_name] = str(value)
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict) and 'text' in value[0]:  # 多选
                        row[field_name] = ', '.join([item['text'] for item in value])
                    else:
                        row[field_name] = ', '.join([str(item) for item in value])
                elif isinstance(value, (int, float)) and field_name.lower() in ['创建时间', '最后更新时间', 'created_time', 'modified_time']:
                    # 时间戳转换
                    try:
                        row[field_name] = datetime.fromtimestamp(value / 1000)
                    except:
                        row[field_name] = value
                else:
                    row[field_name] = value
            
            data_rows.append(row)
        
        return pd.DataFrame(data_rows)
        
    except Exception as e:
        st.error(f"加载数据失败: {str(e)}")
        return None


def render():
    """渲染数据分析页面"""
    st.header("📊 数据分析")
    
    # 检查连接状态
    config = config_manager.get_lark_config()
    
    if not st.session_state.lark_client or not config:
        st.warning("⚠️ 请先在「连接配置」页面配置飞书表格连接")
        
        # 提供快速跳转按钮
        if st.button("🔗 前往连接配置", type="primary"):
            st.switch_page("pages/connection_page.py")
        return
    
    client = st.session_state.lark_client
    
    # 加载数据
    df = load_table_data(client, config.table_id)
    
    if df is None or df.empty:
        st.warning("⚠️ 没有可分析的数据")
        return
    
    st.success(f"✅ 成功加载 {len(df)} 条记录，{len(df.columns)} 个字段")
    
    # 分析选项
    analysis_type = st.radio(
        "选择分析类型",
        options=["数据概览", "字段分析", "趋势分析", "关联分析"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if analysis_type == "数据概览":
        render_data_overview(df)
    elif analysis_type == "字段分析":
        render_field_analysis(df)
    elif analysis_type == "趋势分析":
        render_trend_analysis(df)
    elif analysis_type == "关联分析":
        render_correlation_analysis(df)


def render_data_overview(df: pd.DataFrame):
    """渲染数据概览"""
    st.subheader("📈 数据概览")
    
    # 基本统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("记录总数", len(df))
    with col2:
        st.metric("字段总数", len(df.columns))
    with col3:
        # 计算完整记录数（非空字段数量）
        complete_records = df.dropna(how='any').shape[0]
        st.metric("完整记录", complete_records)
    with col4:
        # 计算数据完整度
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        st.metric("数据完整度", f"{completeness:.1f}%")
    
    # 数据类型分布
    st.subheader("📋 字段类型分布")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 数据类型统计
        dtype_counts = df.dtypes.value_counts()
        
        fig_dtype = px.pie(
            values=dtype_counts.values,
            names=[str(dtype) for dtype in dtype_counts.index],
            title="字段数据类型分布"
        )
        fig_dtype.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_dtype, use_container_width=True)
    
    with col2:
        # 缺失值统计
        missing_data = df.isnull().sum().sort_values(ascending=False)
        missing_data = missing_data[missing_data > 0]
        
        if not missing_data.empty:
            fig_missing = px.bar(
                x=missing_data.values,
                y=missing_data.index,
                orientation='h',
                title="字段缺失值统计",
                labels={'x': '缺失数量', 'y': '字段名称'}
            )
            fig_missing.update_layout(height=400)
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.success("🎉 所有字段都没有缺失值！")
    
    # 数据预览
    st.subheader("👀 数据预览")
    
    # 显示选项
    col1, col2, col3 = st.columns(3)
    with col1:
        show_rows = st.selectbox("显示行数", options=[5, 10, 20, 50], index=1)
    with col2:
        show_info = st.checkbox("显示数据信息", value=True)
    with col3:
        show_describe = st.checkbox("显示统计描述", value=False)
    
    # 数据表格
    st.dataframe(
        df.head(show_rows),
        use_container_width=True,
        hide_index=True
    )
    
    # 数据信息
    if show_info:
        with st.expander("📊 数据信息", expanded=False):
            buffer = []
            buffer.append(f"数据形状: {df.shape}")
            buffer.append(f"内存使用: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            buffer.append("\n字段信息:")
            
            for col in df.columns:
                non_null = df[col].count()
                null_count = len(df) - non_null
                dtype = df[col].dtype
                buffer.append(f"  - {col}: {dtype}, 非空: {non_null}, 缺失: {null_count}")
            
            st.text("\n".join(buffer))
    
    # 统计描述
    if show_describe:
        with st.expander("📈 统计描述", expanded=False):
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                st.dataframe(df[numeric_cols].describe(), use_container_width=True)
            else:
                st.info("没有数值型字段可以进行统计描述")


def render_field_analysis(df: pd.DataFrame):
    """渲染字段分析"""
    st.subheader("🔍 字段分析")
    
    # 字段选择
    selected_field = st.selectbox(
        "选择要分析的字段",
        options=df.columns.tolist(),
        help="选择一个字段进行详细分析"
    )
    
    if not selected_field:
        return
    
    field_data = df[selected_field].dropna()
    
    if field_data.empty:
        st.warning(f"⚠️ 字段 '{selected_field}' 没有有效数据")
        return
    
    # 字段基本信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总数", len(df))
    with col2:
        st.metric("非空数", len(field_data))
    with col3:
        st.metric("缺失数", len(df) - len(field_data))
    with col4:
        unique_count = field_data.nunique()
        st.metric("唯一值", unique_count)
    
    # 根据数据类型进行不同的分析
    if pd.api.types.is_numeric_dtype(field_data):
        render_numeric_field_analysis(field_data, selected_field)
    elif pd.api.types.is_datetime64_any_dtype(field_data):
        render_datetime_field_analysis(field_data, selected_field)
    else:
        render_categorical_field_analysis(field_data, selected_field)


def render_numeric_field_analysis(field_data: pd.Series, field_name: str):
    """数值字段分析"""
    st.subheader(f"📊 数值字段分析: {field_name}")
    
    # 统计指标
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**基本统计:**")
        stats = field_data.describe()
        for stat_name, stat_value in stats.items():
            if isinstance(stat_value, (int, float)):
                st.write(f"- **{stat_name}:** {stat_value:.2f}")
            else:
                st.write(f"- **{stat_name}:** {stat_value}")
    
    with col2:
        st.write("**分布信息:**")
        st.write(f"- **偏度:** {field_data.skew():.3f}")
        st.write(f"- **峰度:** {field_data.kurtosis():.3f}")
        st.write(f"- **变异系数:** {field_data.std() / field_data.mean():.3f}")
        
        # 异常值检测（IQR方法）
        Q1 = field_data.quantile(0.25)
        Q3 = field_data.quantile(0.75)
        IQR = Q3 - Q1
        outliers = field_data[(field_data < Q1 - 1.5 * IQR) | (field_data > Q3 + 1.5 * IQR)]
        st.write(f"- **异常值数量:** {len(outliers)}")
    
    # 可视化
    col1, col2 = st.columns(2)
    
    with col1:
        # 直方图
        fig_hist = px.histogram(
            x=field_data,
            nbins=30,
            title=f"{field_name} - 分布直方图",
            labels={'x': field_name, 'y': '频次'}
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # 箱线图
        fig_box = px.box(
            y=field_data,
            title=f"{field_name} - 箱线图",
            labels={'y': field_name}
        )
        st.plotly_chart(fig_box, use_container_width=True)


def render_datetime_field_analysis(field_data: pd.Series, field_name: str):
    """日期时间字段分析"""
    st.subheader(f"📅 日期字段分析: {field_name}")
    
    # 时间范围
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("最早日期", field_data.min().strftime('%Y-%m-%d'))
    with col2:
        st.metric("最晚日期", field_data.max().strftime('%Y-%m-%d'))
    with col3:
        time_span = (field_data.max() - field_data.min()).days
        st.metric("时间跨度", f"{time_span} 天")
    
    # 时间分布分析
    col1, col2 = st.columns(2)
    
    with col1:
        # 按月分布
        monthly_counts = field_data.dt.to_period('M').value_counts().sort_index()
        
        fig_monthly = px.line(
            x=monthly_counts.index.astype(str),
            y=monthly_counts.values,
            title=f"{field_name} - 按月分布",
            labels={'x': '月份', 'y': '记录数'}
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    with col2:
        # 按星期分布
        weekday_counts = field_data.dt.day_name().value_counts()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_counts = weekday_counts.reindex(weekday_order, fill_value=0)
        
        fig_weekday = px.bar(
            x=weekday_counts.index,
            y=weekday_counts.values,
            title=f"{field_name} - 按星期分布",
            labels={'x': '星期', 'y': '记录数'}
        )
        st.plotly_chart(fig_weekday, use_container_width=True)


def render_categorical_field_analysis(field_data: pd.Series, field_name: str):
    """分类字段分析"""
    st.subheader(f"🏷️ 分类字段分析: {field_name}")
    
    # 值分布统计
    value_counts = field_data.value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**分布统计:**")
        st.write(f"- **唯一值数量:** {len(value_counts)}")
        st.write(f"- **最频繁值:** {value_counts.index[0]}")
        st.write(f"- **最频繁值出现次数:** {value_counts.iloc[0]}")
        st.write(f"- **最频繁值占比:** {value_counts.iloc[0] / len(field_data) * 100:.1f}%")
    
    with col2:
        # 显示前10个值
        st.write("**前10个值:**")
        top_values = value_counts.head(10)
        for value, count in top_values.items():
            percentage = count / len(field_data) * 100
            st.write(f"- **{value}:** {count} ({percentage:.1f}%)")
    
    # 可视化
    col1, col2 = st.columns(2)
    
    with col1:
        # 条形图（前15个值）
        top_15 = value_counts.head(15)
        
        fig_bar = px.bar(
            x=top_15.values,
            y=top_15.index,
            orientation='h',
            title=f"{field_name} - 值分布（前15）",
            labels={'x': '数量', 'y': '值'}
        )
        fig_bar.update_layout(height=500)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # 饼图（前10个值）
        top_10 = value_counts.head(10)
        others_count = value_counts.iloc[10:].sum() if len(value_counts) > 10 else 0
        
        if others_count > 0:
            pie_data = list(top_10.values) + [others_count]
            pie_labels = list(top_10.index) + ['其他']
        else:
            pie_data = top_10.values
            pie_labels = top_10.index
        
        fig_pie = px.pie(
            values=pie_data,
            names=pie_labels,
            title=f"{field_name} - 值分布饼图"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)


def render_trend_analysis(df: pd.DataFrame):
    """渲染趋势分析"""
    st.subheader("📈 趋势分析")
    
    # 查找日期字段
    date_columns = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or '时间' in col or 'date' in col.lower():
            date_columns.append(col)
    
    if not date_columns:
        st.warning("⚠️ 未找到日期字段，无法进行趋势分析")
        return
    
    # 选择日期字段
    date_field = st.selectbox("选择日期字段", options=date_columns)
    
    if not date_field:
        return
    
    # 处理日期数据
    df_trend = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_trend[date_field]):
        try:
            # 尝试转换时间戳
            df_trend[date_field] = pd.to_datetime(df_trend[date_field], unit='ms', errors='coerce')
        except:
            try:
                # 尝试直接转换
                df_trend[date_field] = pd.to_datetime(df_trend[date_field], errors='coerce')
            except:
                st.error(f"❌ 无法解析日期字段 '{date_field}'")
                return
    
    # 过滤有效日期
    df_trend = df_trend.dropna(subset=[date_field])
    
    if df_trend.empty:
        st.warning("⚠️ 没有有效的日期数据")
        return
    
    # 时间粒度选择
    time_granularity = st.selectbox(
        "选择时间粒度",
        options=["日", "周", "月", "季度", "年"],
        index=2
    )
    
    # 按时间粒度聚合
    if time_granularity == "日":
        df_trend['period'] = df_trend[date_field].dt.date
    elif time_granularity == "周":
        df_trend['period'] = df_trend[date_field].dt.to_period('W')
    elif time_granularity == "月":
        df_trend['period'] = df_trend[date_field].dt.to_period('M')
    elif time_granularity == "季度":
        df_trend['period'] = df_trend[date_field].dt.to_period('Q')
    elif time_granularity == "年":
        df_trend['period'] = df_trend[date_field].dt.to_period('Y')
    
    # 记录数趋势
    trend_counts = df_trend.groupby('period').size().reset_index(name='count')
    trend_counts['period_str'] = trend_counts['period'].astype(str)
    
    fig_trend = px.line(
        trend_counts,
        x='period_str',
        y='count',
        title=f"记录数趋势 - 按{time_granularity}",
        labels={'period_str': f'时间({time_granularity})', 'count': '记录数'}
    )
    fig_trend.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # 数值字段趋势分析
    numeric_columns = df_trend.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_columns:
        st.subheader("📊 数值字段趋势")
        
        selected_numeric = st.selectbox("选择数值字段", options=numeric_columns)
        
        if selected_numeric:
            # 按时间聚合数值字段
            numeric_trend = df_trend.groupby('period')[selected_numeric].agg(['mean', 'sum', 'count']).reset_index()
            numeric_trend['period_str'] = numeric_trend['period'].astype(str)
            
            # 创建子图
            fig_numeric = make_subplots(
                rows=2, cols=2,
                subplot_titles=('平均值趋势', '总和趋势', '记录数趋势', '累计趋势'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # 平均值趋势
            fig_numeric.add_trace(
                go.Scatter(x=numeric_trend['period_str'], y=numeric_trend['mean'], 
                          mode='lines+markers', name='平均值'),
                row=1, col=1
            )
            
            # 总和趋势
            fig_numeric.add_trace(
                go.Scatter(x=numeric_trend['period_str'], y=numeric_trend['sum'], 
                          mode='lines+markers', name='总和'),
                row=1, col=2
            )
            
            # 记录数趋势
            fig_numeric.add_trace(
                go.Scatter(x=numeric_trend['period_str'], y=numeric_trend['count'], 
                          mode='lines+markers', name='记录数'),
                row=2, col=1
            )
            
            # 累计趋势
            cumulative_sum = numeric_trend['sum'].cumsum()
            fig_numeric.add_trace(
                go.Scatter(x=numeric_trend['period_str'], y=cumulative_sum, 
                          mode='lines+markers', name='累计'),
                row=2, col=2
            )
            
            fig_numeric.update_layout(height=600, title_text=f"{selected_numeric} - 多维度趋势分析")
            fig_numeric.update_xaxes(tickangle=-45)
            st.plotly_chart(fig_numeric, use_container_width=True)


def render_correlation_analysis(df: pd.DataFrame):
    """渲染关联分析"""
    st.subheader("🔗 关联分析")
    
    # 数值字段相关性分析
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_columns) < 2:
        st.warning("⚠️ 需要至少2个数值字段才能进行相关性分析")
    else:
        st.subheader("📊 数值字段相关性")
        
        # 计算相关性矩阵
        correlation_matrix = df[numeric_columns].corr()
        
        # 相关性热力图
        fig_corr = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title="字段相关性热力图",
            color_continuous_scale='RdBu_r'
        )
        fig_corr.update_layout(height=500)
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # 强相关性对
        st.subheader("🔍 强相关性字段对")
        
        # 找出强相关性（绝对值 > 0.7）
        strong_correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    strong_correlations.append({
                        '字段1': correlation_matrix.columns[i],
                        '字段2': correlation_matrix.columns[j],
                        '相关系数': corr_value,
                        '相关强度': '强正相关' if corr_value > 0.7 else '强负相关'
                    })
        
        if strong_correlations:
            st.dataframe(pd.DataFrame(strong_correlations), use_container_width=True, hide_index=True)
        else:
            st.info("📝 未发现强相关性字段对（|相关系数| > 0.7）")
    
    # 分类字段关联分析
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(categorical_columns) >= 2:
        st.subheader("🏷️ 分类字段关联")
        
        col1, col2 = st.columns(2)
        with col1:
            field1 = st.selectbox("选择字段1", options=categorical_columns, key="cat1")
        with col2:
            field2 = st.selectbox("选择字段2", options=[col for col in categorical_columns if col != field1], key="cat2")
        
        if field1 and field2:
            # 交叉表分析
            crosstab = pd.crosstab(df[field1], df[field2])
            
            # 热力图
            fig_cross = px.imshow(
                crosstab.values,
                x=crosstab.columns,
                y=crosstab.index,
                text_auto=True,
                aspect="auto",
                title=f"{field1} vs {field2} - 交叉分析",
                labels={'x': field2, 'y': field1}
            )
            st.plotly_chart(fig_cross, use_container_width=True)
            
            # 卡方检验
            try:
                from scipy.stats import chi2_contingency
                chi2, p_value, dof, expected = chi2_contingency(crosstab)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("卡方统计量", f"{chi2:.4f}")
                with col2:
                    st.metric("P值", f"{p_value:.4f}")
                with col3:
                    significance = "显著" if p_value < 0.05 else "不显著"
                    st.metric("关联性", significance)
                
            except ImportError:
                st.info("💡 安装 scipy 库可以进行卡方检验分析")
            except Exception as e:
                st.warning(f"⚠️ 卡方检验失败: {str(e)}")
    
    # 数值与分类字段关联
    if numeric_columns and categorical_columns:
        st.subheader("📈 数值-分类字段关联")
        
        col1, col2 = st.columns(2)
        with col1:
            numeric_field = st.selectbox("选择数值字段", options=numeric_columns, key="num_cat")
        with col2:
            categorical_field = st.selectbox("选择分类字段", options=categorical_columns, key="cat_num")
        
        if numeric_field and categorical_field:
            # 按分类分组的数值分布
            fig_box_cat = px.box(
                df,
                x=categorical_field,
                y=numeric_field,
                title=f"{numeric_field} 在不同 {categorical_field} 下的分布"
            )
            fig_box_cat.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_box_cat, use_container_width=True)
            
            # 统计摘要
            group_stats = df.groupby(categorical_field)[numeric_field].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
            st.dataframe(group_stats, use_container_width=True)
