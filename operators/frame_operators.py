import bpy
from bpy.utils import register_class, unregister_class
from ..i18n.translation import get_text


def stop_playback(scene):
    """停止播放回调"""
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=False)
    print("Stop Loop")


def start_playback(scene):
    """开始播放回调"""
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=True)
    print("Start Loop")


class FrameStartOperator(bpy.types.Operator):
    """设置开始帧"""
    bl_idname = "frame.set_start"
    bl_label = "SetStartFrame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        try:
            import bpy
            actscene = bpy.context.scene
            bpy.data.scenes[actscene.name].frame_start = bpy.data.scenes[actscene.name].frame_current
        except Exception as exc:
            print(str(exc) + " | Error in execute function of SetStartFrame")
        return {"FINISHED"}

    def invoke(self, context, event):
        try:
            pass
        except Exception as exc:
            print(str(exc) + " | Error in invoke function of SetStartFrame")
        return self.execute(context)


class FrameEndOperator(bpy.types.Operator):
    """设置结束帧"""
    bl_idname = "frame.set_end"
    bl_label = "SetEndFrame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        try:
            import bpy
            actscene = bpy.context.scene
            bpy.data.scenes[actscene.name].frame_end = bpy.data.scenes[actscene.name].frame_current
        except Exception as exc:
            print(str(exc) + " | Error in execute function of SetEndFrame")
        return {"FINISHED"}

    def invoke(self, context, event):
        try:
            pass
        except Exception as exc:
            print(str(exc) + " | Error in invoke function of SetEndFrame")
        return self.execute(context)


class FrameLoopOperator(bpy.types.Operator):
    """设置循环播放"""
    bl_idname = "frame.toggle_loop"
    bl_label = "StopLoop"

    def execute(self, context):
        frame_change = bpy.app.handlers.frame_change_pre
        actscene = bpy.context.scene

        if stop_playback not in frame_change:
            stop_playback(bpy.data.scenes[actscene.name])
            frame_change.append(stop_playback)
        elif stop_playback in frame_change:
            start_playback(bpy.data.scenes[actscene.name])
            del frame_change[-1]

        print(list(frame_change))
        return {'FINISHED'}


class LanguageToggleOperator(bpy.types.Operator):
    """切换语言"""
    bl_idname = "ui.toggle_language"
    bl_label = "切换中英文"

    def execute(self, context):
        viewlanguage = context.preferences.view.language
        prefview = context.preferences.view
        
        # 确定当前语言和目标语言
        if viewlanguage != "en_US":
            current_lang = "中文"
            target_lang = "English"
            context.preferences.view.language = "en_US"
        else:
            current_lang = "English"
            target_lang = "中文"
            try:
                context.preferences.view.language = "zh_CN"
            except:
                context.preferences.view.language = "zh_HANS"
            prefview.use_translate_new_dataname = False
        
        # 输出日志信息
        print(f"ATools语言切换: {current_lang} → {target_lang}")
        
        return {'FINISHED'}


classes = (
    FrameStartOperator,
    FrameEndOperator,
    FrameLoopOperator,
    LanguageToggleOperator,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 