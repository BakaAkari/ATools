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
    # 1. 先注册属性组
    property_groups.register()
    
    # 2. 添加嵌套属性（在类上添加，注册后立即添加）
    AToolsToolProperties = property_groups.AToolsToolProperties
    AToolsToolProperties.atex_props = PointerProperty(type=property_groups.ATexProperties)
    AToolsToolProperties.explode_props = PointerProperty(type=property_groups.ExplodeProperties)
    
    # 3. 注册WindowManager的属性
    bpy.types.WindowManager.atprops = PointerProperty(type=property_groups.AToolsToolProperties)
    
    # 4. 注册操作符（必须先注册，UI才能引用）
    mesh_operators.register()
    node_operators.register()
    physics_operators.register()
    frame_operators.register()  # 包含 LanguageToggleOperator
    atex_operators.register()
    collection_operators.register()
    
    # 5. 注册UI
    panels.register()
    preferences.register()
    
    # 6. 添加UI回调函数（最后添加，确保所有依赖都已注册）
    try:
        bpy.types.STATUSBAR_HT_header.append(ui_functions.translation_ui_function)
        bpy.types.DOPESHEET_HT_header.append(ui_functions.frame_ui_function)
        bpy.types.NODE_HT_header.append(ui_functions.reload_image_ui_function)
        print("ATools: UI callbacks registered successfully")
    except Exception as e:
        print(f"ATools: Error registering UI callbacks: {e}")


def unregister():
    """注销所有模块"""
    # 移除UI回调函数
    try:
        bpy.types.STATUSBAR_HT_header.remove(ui_functions.translation_ui_function)
        bpy.types.DOPESHEET_HT_header.remove(ui_functions.frame_ui_function)
        bpy.types.NODE_HT_header.remove(ui_functions.reload_image_ui_function)
    except Exception as e:
        print(f"ATools: Error removing UI callbacks: {e}")
    
    # 注销UI
    preferences.unregister()
    panels.unregister()
    
    # 注销操作符
    mesh_operators.unregister()
    node_operators.unregister()
    physics_operators.unregister()
    frame_operators.unregister()
    atex_operators.unregister()
    collection_operators.unregister()
    
    # 移除WindowManager属性
    try:
        del bpy.types.WindowManager.atprops
    except:
        pass
    
    # 注销属性组（会自动清理所有关联的属性）
    property_groups.unregister()


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()

