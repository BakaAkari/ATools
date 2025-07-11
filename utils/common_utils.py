import bpy
import os
import subprocess
import numpy as np


class ATError(Exception):
    """ATools 基础异常类"""
    pass


class ATFileError(ATError):
    """文件操作相关异常"""
    pass


class ATOperationError(ATError):
    """操作执行相关异常"""
    pass


def safe_execute(operation, error_message="操作失败", logger=None):
    """安全执行操作的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.error(f"{error_message}: {str(e)}")
                else:
                    print(f"{error_message}: {str(e)}")
                raise ATOperationError(f"{error_message}: {str(e)}")
        return wrapper
    return decorator


def messagebox(message="", title="WARNING", icon='INFO'):
    """显示消息框"""
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def open_system_directory(path):
    """打开系统目录"""
    try:
        if not os.path.exists(path):
            raise ATFileError(f"路径不存在: {path}")
            
        if os.name == 'nt':  # Windows
            subprocess.run(['explorer', os.path.dirname(path)])
        elif os.name == 'posix':  # Linux or macOS
            subprocess.run(['xdg-open', os.path.dirname(path)])
        else:
            raise ATOperationError(f"不支持的操作系统: {os.name}")
    except Exception as e:
        raise ATFileError(f"无法打开目录: {str(e)}")


def validate_object_selection(context, min_count=1, obj_type='MESH'):
    """验证对象选择"""
    selected_objs = [obj for obj in context.selected_objects if obj.type == obj_type]
    if len(selected_objs) < min_count:
        raise ATOperationError(f"需要选择至少 {min_count} 个 {obj_type} 对象")
    return selected_objs


def get_active_material_nodes(obj):
    """安全获取活动材质节点"""
    if not obj or not obj.active_material:
        raise ATOperationError("对象没有活动材质")
    
    if not obj.active_material.node_tree:
        raise ATOperationError("材质没有节点树")
        
    return obj.active_material.node_tree.nodes 