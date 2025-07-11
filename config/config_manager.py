# 配置管理系统
import bpy
import json
import os
from typing import Dict, Any, Optional
from ..utils.common_utils import ATError, ATFileError

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, addon_name: str = "ATools"):
        self.addon_name = addon_name
        self._config_file = self._get_config_file_path()
        self._default_config = self._get_default_config()
        self._current_config = self._load_config()
    
    def _get_config_file_path(self) -> str:
        """获取配置文件路径"""
        # 获取Blender用户配置目录
        config_dir = bpy.utils.user_resource('CONFIG')
        addon_config_dir = os.path.join(config_dir, 'addons', self.addon_name)
        
        # 确保目录存在
        os.makedirs(addon_config_dir, exist_ok=True)
        
        return os.path.join(addon_config_dir, 'config.json')
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'render': {
                'eevee': {
                    'taa_samples': 0,
                    'taa_render_samples': 512,
                    'gtao_quality': 1,
                    'use_raytracing': True,
                    'volumetric_tile_size': '4',
                    'volumetric_sample_distribution': 1,
                    'volumetric_shadow_samples': 64,
                    'shadow_ray_count': 3
                },
                'cycles': {
                    'preview_adaptive_threshold': 0.01,
                    'use_preview_denoising': True,
                    'tile_size': 512,
                    'device': 'GPU'
                },
                'common': {
                    'look': 'AgX - High Contrast',
                    'compression': 0,
                    'use_high_quality_normals': True
                }
            },
            'physics': {
                'default_friction': 0.5,
                'default_time_scale': 5.0,
                'max_simulation_frames': 10000,
                'collision_margin': 0.0001
            },
            'export': {
                'default_rule': 'UNREAL',
                'default_path': '',
                'unreal_axis_forward': '-Z',
                'unreal_axis_up': 'Y',
                'unity_axis_forward': 'X',
                'unity_axis_up': 'Y'
            },
            'ui': {
                'language': 'auto',  # 'auto', 'en_US', 'zh_HANS'
                'panel_category': 'Tool',
                'show_advanced_options': False
            },
            'preferences': {
                'viewport_aa': '32',
                'anisotropic_filter': 'FILTER_16',
                'undo_steps': 256,
                'auto_save_config': True
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    return self._merge_config(self._default_config, loaded_config)
            else:
                return self._default_config.copy()
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            return self._default_config.copy()
    
    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置，确保所有默认值都存在"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_config(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def save_config(self) -> bool:
        """保存配置"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._current_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值（支持点分隔的路径）"""
        keys = key_path.split('.')
        current = self._current_config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, auto_save: bool = None) -> bool:
        """设置配置值（支持点分隔的路径）"""
        keys = key_path.split('.')
        current = self._current_config
        
        try:
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置值
            current[keys[-1]] = value
            
            # 自动保存
            if auto_save is None:
                auto_save = self.get('preferences.auto_save_config', True)
            
            if auto_save:
                return self.save_config()
            
            return True
        except Exception as e:
            print(f"设置配置失败: {str(e)}")
            return False
    
    def reset_to_default(self, section: Optional[str] = None) -> bool:
        """重置配置到默认值"""
        try:
            if section:
                if section in self._default_config:
                    self._current_config[section] = self._default_config[section].copy()
                else:
                    return False
            else:
                self._current_config = self._default_config.copy()
            
            return self.save_config()
        except Exception as e:
            print(f"重置配置失败: {str(e)}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """导出配置到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._current_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {str(e)}")
            return False
    
    def import_config(self, file_path: str, merge: bool = True) -> bool:
        """从文件导入配置"""
        try:
            if not os.path.exists(file_path):
                raise ATFileError(f"配置文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            if merge:
                self._current_config = self._merge_config(self._current_config, imported_config)
            else:
                self._current_config = imported_config
            
            return self.save_config()
        except Exception as e:
            print(f"导入配置失败: {str(e)}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'config_file': self._config_file,
            'config_exists': os.path.exists(self._config_file),
            'sections': list(self._current_config.keys()),
            'auto_save': self.get('preferences.auto_save_config', True)
        }


# 全局配置管理器实例
_config_manager = ConfigManager()

def get_config(key_path: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return _config_manager.get(key_path, default)

def set_config(key_path: str, value: Any, auto_save: bool = None) -> bool:
    """设置配置值的便捷函数"""
    return _config_manager.set(key_path, value, auto_save)

def save_config() -> bool:
    """保存配置的便捷函数"""
    return _config_manager.save_config()

def reset_config(section: Optional[str] = None) -> bool:
    """重置配置的便捷函数"""
    return _config_manager.reset_to_default(section) 