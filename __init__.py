import bpy
from bpy.app.handlers import persistent
from bpy.props import PointerProperty

# 导入所有新模块
from . import (
    operators,
    ui,
    properties,
    config,
    i18n
)

# 导入具体模块
from .operators import (
    mesh_operators,
    node_operators,
    physics_operators,
    frame_operators,
    atex_operators,
    collection_operators
)

from .ui import (
    panels,
    preferences,
    ui_functions
)

from .properties import property_groups
from .config import constants
from .i18n import translation

# 插件信息
bl_info = {
    "name": "ATools",
    "description": "Baka_Akari's fixed Quixel Bridge Link plugin suite",
    "author": "Baka_Akari",
    "version": (0, 0, 9),
    "blender": (2, 8, 0),
    "location": "View3D",
    "warning": "Multiple functions are in beta.",
    "wiki_url": "https://docs.quixel.org/bridge/livelinks/blender/info_quickstart.html",
    "support": "COMMUNITY",
    "category": "3D View"
}


def register():
    """注册所有模块"""
    # 注册属性组
    property_groups.register()
    
    # 注册操作符
    mesh_operators.register()
    node_operators.register()
    physics_operators.register()
    frame_operators.register()
    atex_operators.register()
    collection_operators.register()
    
    # 注册UI
    panels.register()
    preferences.register()
    
    # 注册属性到WindowManager
    bpy.types.WindowManager.atprops = PointerProperty(type=property_groups.ToolProperties)
    bpy.types.WindowManager.quick_physics = PointerProperty(type=property_groups.ToolProperties)
    bpy.types.WindowManager.atex_props = PointerProperty(type=property_groups.ATexProperties)
    
    # 添加UI回调函数
    bpy.types.STATUSBAR_HT_header.append(ui_functions.translation_ui_function)
    bpy.types.DOPESHEET_HT_header.append(ui_functions.frame_ui_function)
    bpy.types.NODE_HT_header.append(ui_functions.reload_image_ui_function)


def unregister():
    """注销所有模块"""
    # 注销UI
    preferences.unregister()
    panels.unregister()
    
    # 注销操作符
    frame_operators.unregister()
    physics_operators.unregister()
    node_operators.unregister()
    mesh_operators.unregister()
    atex_operators.unregister()
    collection_operators.unregister()
    
    # 注销属性组
    property_groups.unregister()
    
    # 移除属性
    del bpy.types.WindowManager.atprops
    del bpy.types.WindowManager.quick_physics
    del bpy.types.WindowManager.atex_props
    
    # 移除UI回调函数
    bpy.types.STATUSBAR_HT_header.remove(ui_functions.translation_ui_function)
    bpy.types.DOPESHEET_HT_header.remove(ui_functions.frame_ui_function)
    bpy.types.NODE_HT_header.remove(ui_functions.reload_image_ui_function)


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()

