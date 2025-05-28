import bpy
import os
import subprocess
import numpy as np

def is_pil_available():
    """检查PIL库是否可用"""
    try:
        import PIL
        return True
    except ImportError:
        return False

def check_pil_required(func):
    """装饰器：检查PIL是否可用，如果不可用则显示警告并返回None"""
    def wrapper(*args, **kwargs):
        if not is_pil_available():
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text="This feature requires PIL library. Please install it from the plugin settings."),
                title="WARNING",
                icon='INFO'
            )
            return None
        return func(*args, **kwargs)
    return wrapper

def messagebox(message="", title="WARNING", icon='INFO'):
    """显示消息框"""
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def open_system_directory(path):
    """打开系统目录"""
    if os.name == 'nt':  # Windows
        subprocess.run(['explorer', os.path.dirname(path)])
    elif os.name == 'posix':  # Linux or macOS
        subprocess.run(['xdg-open', os.path.dirname(path)])

@check_pil_required
def convert_blender_image_to_pil(tex_node):
    """将Blender图像转换为PIL图像"""
    try:
        from PIL import Image
    except:
        pass

    blender_image = tex_node.image
    width, height = blender_image.size
    pixels = np.array(blender_image.pixels).reshape(height, width, 4)
    pil_image = Image.fromarray((pixels * 255).astype(np.uint8))
    return pil_image 