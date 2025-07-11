import bpy
from bpy.types import AddonPreferences, PropertyGroup
from bpy.utils import register_class, unregister_class
from ..i18n.translation import get_text


class ToolAddonPreferences(AddonPreferences):
    """插件偏好设置"""
    bl_idname = __package__.split('.')[0]  # 获取插件包名

    def draw(self, context):
        layout: bpy.types.UILayout
        
        wm = context.window_manager
        props = wm.atprops


classes = (ToolAddonPreferences,)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 