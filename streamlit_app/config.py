"""
Streamlit 应用配置管理模块

提供配置加载、验证和管理功能
"""

import os
import yaml
import streamlit as st
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class LarkConfig:
    """飞书配置数据类"""
    personal_token: str = ""
    app_token: str = ""
    table_id: str = ""
    domain: str = "https://base-api.feishu.cn"
    
    def is_valid(self) -> bool:
        """验证配置是否有效"""
        return (
            bool(self.personal_token and self.personal_token.startswith('pt-')) and
            bool(self.app_token) and
            bool(self.table_id)
        )


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.production_config_path = self.config_dir / "production.yaml"
        self.default_config_path = self.config_dir / "default.yaml"
        self._load_configs()
    
    def _load_configs(self) -> None:
        """加载配置文件"""
        # 优先加载 production.yaml
        self.production_config = {}
        if self.production_config_path.exists():
            with open(self.production_config_path, 'r', encoding='utf-8') as f:
                self.production_config = yaml.safe_load(f) or {}
        
        # 加载 default.yaml 作为备用
        self.default_config = {}
        if self.default_config_path.exists():
            with open(self.default_config_path, 'r', encoding='utf-8') as f:
                self.default_config = yaml.safe_load(f) or {}
    
    def get_default_lark_config(self) -> Optional[LarkConfig]:
        """从 production.yaml 获取默认飞书配置"""
        # 优先从 production.yaml 读取
        config_source = self.production_config if self.production_config else self.default_config
        
        if config_source:
            try:
                return LarkConfig(
                    personal_token=config_source.get('personal_token', ''),
                    app_token=config_source.get('app_token', ''),
                    table_id=config_source.get('table_id', ''),
                    domain=config_source.get('domain', 'https://base-api.feishu.cn')
                )
            except Exception as e:
                st.error(f"读取默认配置失败: {str(e)}")
        return None
    
    def get_lark_config(self) -> Optional[LarkConfig]:
        """从 Streamlit session state 获取飞书配置，如果没有则使用默认配置"""
        if 'lark_config' in st.session_state:
            config_dict = st.session_state.lark_config
            return LarkConfig(**config_dict)
        
        # 如果 session state 中没有配置，尝试加载默认配置
        default_config = self.get_default_lark_config()
        if default_config and default_config.is_valid():
            self.save_lark_config(default_config)
            return default_config
        
        return None
    
    def save_lark_config(self, config: LarkConfig) -> None:
        """保存飞书配置到 session state"""
        st.session_state.lark_config = {
            'personal_token': config.personal_token,
            'app_token': config.app_token,
            'table_id': config.table_id,
            'domain': config.domain
        }
    
    def save_lark_config_to_yaml(self, config: LarkConfig) -> bool:
        """保存飞书配置到 production.yaml 文件"""
        try:
            # 读取现有的 production.yaml 内容
            config_data = {}
            if self.production_config_path.exists():
                with open(self.production_config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
            
            # 更新飞书配置部分
            config_data.update({
                'personal_token': config.personal_token,
                'app_token': config.app_token,
                'table_id': config.table_id,
                'domain': config.domain
            })
            
            # 写回文件
            with open(self.production_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            # 重新加载配置
            self._load_configs()
            
            return True
        except Exception as e:
            st.error(f"保存配置到 YAML 文件失败: {str(e)}")
            return False
    
    def get_field_mappings(self) -> Dict[str, str]:
        """获取字段映射配置"""
        return self.default_config.get('field_mappings', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return {
            'request_timeout': self.default_config.get('request_timeout', 30),
            'max_retries': self.default_config.get('max_retries', 3),
            'retry_delay': self.default_config.get('retry_delay', 1.0),
            'max_response_length': self.default_config.get('max_response_length', 2000)
        }


# 全局配置管理器实例
config_manager = ConfigManager()


def init_session_state() -> None:
    """初始化 Streamlit session state"""
    if 'lark_client' not in st.session_state:
        st.session_state.lark_client = None
    
    if 'lark_config' not in st.session_state:
        # 尝试从配置文件加载默认配置
        default_config = config_manager.get_default_lark_config()
        if default_config and default_config.is_valid():
            config_manager.save_lark_config(default_config)
        else:
            st.session_state.lark_config = None
    
    if 'current_table_data' not in st.session_state:
        st.session_state.current_table_data = None
    
    if 'table_fields' not in st.session_state:
        st.session_state.table_fields = []
    
    if 'selected_records' not in st.session_state:
        st.session_state.selected_records = []


def clear_session_state() -> None:
    """清除 session state"""
    keys_to_clear = [
        'lark_client', 
        'lark_config',
        'current_table_data', 
        'table_fields',
        'selected_records'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
