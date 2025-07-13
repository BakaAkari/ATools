import bpy
from bpy.types import AddonPreferences, PropertyGroup
from bpy.utils import register_class, unregister_class
from ..i18n.translation import get_text


class ToolAddonPreferences(AddonPreferences):
    """插件偏好设置"""
    bl_idname = __package__.split('.')[0]  # 获取插件包名

    def draw(self, context):
        layout = self.layout
        
        wm = context.window_manager
        props = wm.atprops
        atex_props = wm.atex_props
        
        # ATex设置
        box = layout.box()
        box.label(text="ATex设置")
        
        # 启用ATex功能复选框
        box.prop(atex_props, 'enable_atex', text="启用ATex图像处理功能")
        
        # 如果启用了ATex功能，显示路径选择
        if atex_props.enable_atex:
            box.prop(atex_props, 'atex_exe_path', text="ATex.exe路径")


classes = (ToolAddonPreferences,)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 