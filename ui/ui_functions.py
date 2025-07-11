import bpy
from ..i18n.translation import get_text
from ..operators.frame_operators import stop_playback, start_playback


def translation_ui_function(self, context):
    """翻译切换UI函数"""
    layout = self.layout
    if context.preferences.view.language == "en_US":
        buttonname = get_text("Switch CH", context)
    else:
        buttonname = get_text("切换英文", context)
        
    layout.operator(operator="ui.toggle_language", text=buttonname)


def reload_image_ui_function(self, context):
    """重载图像UI函数"""
    layout = self.layout
    layout.separator()
    layout.operator(operator="image.reload_all", text=get_text("Reload Images", context), icon='FILE_REFRESH')


def frame_ui_function(self, context):
    """帧控制UI函数"""
    try:
        layout = self.layout
        layout.operator("frame.set_start", text=get_text("Start", context), emboss=True, depress=False, icon_value=0)
        layout.operator("frame.set_end", text=get_text("End", context), emboss=True, depress=False, icon_value=0)
        layout.operator("frame.toggle_loop", text=get_text("Set Loop", context), emboss=True, depress=False, icon_value=0)

    except Exception as exc:
        print(str(exc) + " | Error in Dopesheet Ht Header when adding to menu") 