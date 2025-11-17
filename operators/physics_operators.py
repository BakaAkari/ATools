import bpy
from bpy.utils import register_class, unregister_class
from mathutils import Matrix
from ..i18n.translation import get_text
from ..config.constants import PhysicsSettings
from ..utils.common_utils import ATOperationError, validate_object_selection


def get_atprops(context):
    """安全获取 atprops 属性"""
    wm = context.window_manager
    if not hasattr(wm, 'atprops'):
        raise AttributeError(
            "WindowManager 缺少 'atprops' 属性。"
            "请确保插件已正确注册。"
            "尝试重新加载插件。"
        )
    if wm.atprops is None:
        raise AttributeError(
            "WindowManager.atprops 为 None。"
            "请确保插件已正确初始化。"
        )
    return wm.atprops


class PhysicsCalculateOperator(bpy.types.Operator):
    """计算物理模拟"""
    bl_idname = "physics.calculate"
    bl_label = "Calculate Physics"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def add_passive_bodies(self, context, add):
        """添加或移除被动刚体"""
        atprops = get_atprops(context)
        active_object = context.active_object

        for obj in context.visible_objects:
            if not obj.select_get() and obj.type == "MESH":
                context.view_layer.objects.active = obj
                if add and obj.rigid_body == None:
                    bpy.ops.rigidbody.object_add()
                    obj.rigid_body.friction = atprops.physics_friction
                    obj.rigid_body.use_margin = True
                    obj.rigid_body.collision_margin = PhysicsSettings.COLLISION_MARGIN
                    obj.rigid_body.type = "PASSIVE"
                    obj.rigid_body.collision_shape = "MESH"
                elif not add and obj.rigid_body != None:
                    bpy.ops.rigidbody.object_remove()

        context.view_layer.objects.active = active_object

    def invoke(self, context, event):
        try:
            # 验证选择的对象
            selected_objects = validate_object_selection(context, min_count=1, obj_type='MESH')
            
            # Initialize variables here instead of in __init__
            self.fps = 0
            self.frame_start = 0
            self.frame_end = 0
            self.frame_current = 0
            self.world_enabled = True
            self.use_split_impulse = True
            self.world_time_scale = 1.0

            wm = context.window_manager
            atprops = get_atprops(context)
            wm.modal_handler_add(self)
            atprops.running_physics_calculation = True

            # 确保刚体世界存在
            if context.scene.rigidbody_world == None:
                bpy.ops.rigidbody.world_add()

            # 保存当前设置
            scene = context.scene
            self.fps = scene.render.fps
            self.frame_start = scene.frame_start
            self.frame_end = scene.frame_end
            self.frame_current = scene.frame_current
            self.world_enabled = scene.rigidbody_world.enabled
            self.use_split_impulse = scene.rigidbody_world.use_split_impulse
            self.world_time_scale = scene.rigidbody_world.time_scale

            # 应用物理模拟设置
            scene.rigidbody_world.time_scale = atprops.physics_time_scale
            scene.render.fps = PhysicsSettings.DEFAULT_FPS
            scene.frame_start = 0
            scene.frame_end = PhysicsSettings.MAX_SIMULATION_FRAMES
            scene.frame_current = 0
            scene.rigidbody_world.enabled = True
            scene.rigidbody_world.use_split_impulse = True

            # 添加被动刚体
            self.add_passive_bodies(context, True)

            # 为选中对象添加主动物理
            bpy.ops.physics.add_active()

            # 开始播放动画
            bpy.ops.screen.animation_play()

            # 开始进度条
            tot = scene.frame_end
            wm.progress_begin(0, tot)
            
            self.report({'INFO'}, f"开始物理模拟 ({len(selected_objects)} 个对象)")
            return {"RUNNING_MODAL"}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {"CANCELLED"}
        except Exception as e:
            self.report({'ERROR'}, f"启动物理模拟失败: {str(e)}")
            return {"CANCELLED"}

    def exit_modal(self, context, wm):
        """退出模态操作"""
        atprops = get_atprops(context)
        atprops.running_physics_calculation = False
        bpy.ops.screen.animation_play()
        bpy.ops.physics.apply()

        context.scene.render.fps = self.fps
        context.scene.frame_start = self.frame_start
        context.scene.frame_end = self.frame_end
        context.scene.frame_current = self.frame_current
        context.scene.rigidbody_world.enabled = self.world_enabled
        context.scene.rigidbody_world.use_split_impulse = self.use_split_impulse
        context.scene.rigidbody_world.time_scale = self.world_time_scale

        self.add_passive_bodies(context, False)
        wm.progress_end()
        bpy.ops.ed.undo_push(message="Calc Physics")

    def modal(self, context, event):
        """模态操作循环"""
        wm = context.window_manager
        atprops = get_atprops(context)
        if event.type in {"ESC"} or context.scene.frame_current >= PhysicsSettings.MAX_SIMULATION_FRAMES or not atprops.running_physics_calculation:
            self.exit_modal(context, wm)
            return {"CANCELLED"}
        wm.progress_update(context.scene.frame_current)
        return {"PASS_THROUGH"}


class PhysicsAddActiveOperator(bpy.types.Operator):
    """为选中对象添加主动物理属性"""
    bl_idname = "physics.add_active"
    bl_label = "Add physics to Assets"
    bl_description = "Sets up Assets as rigidbody objects."

    def execute(self, context):
        try:
            # 验证对象选择
            selected_objects = validate_object_selection(context, min_count=1, obj_type='MESH')
            
            atprops = get_atprops(context)
            active_object = context.active_object
            processed_count = 0
            failed_objects = []
            
            for obj in selected_objects:
                try:
                    context.view_layer.objects.active = obj
                    bpy.ops.rigidbody.object_add()
                    obj.rigid_body.friction = atprops.physics_friction
                    obj.rigid_body.use_margin = True
                    obj.rigid_body.collision_margin = PhysicsSettings.COLLISION_MARGIN
                    processed_count += 1
                except Exception as e:
                    failed_objects.append(f"{obj.name}: {str(e)}")
            
            # 恢复活动对象
            context.view_layer.objects.active = active_object
            
            # 报告结果
            if processed_count > 0:
                self.report({'INFO'}, f"成功为 {processed_count} 个对象添加物理属性")
            
            if failed_objects:
                error_msg = "添加物理属性失败的对象:\n" + "\n".join(failed_objects[:3])
                if len(failed_objects) > 3:
                    error_msg += f"\n... 还有 {len(failed_objects) - 3} 个对象失败"
                self.report({'WARNING'}, error_msg)

            return {'FINISHED'}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"添加物理属性失败: {str(e)}")
            return {'CANCELLED'}


class PhysicsApplyOperator(bpy.types.Operator):
    """应用物理模拟结果"""
    bl_idname = "physics.apply"
    bl_label = "Apply physics to Assets"
    bl_description = "Applies physics to assets and removes rigidbodies."

    def execute(self, context):
        try:
            # 验证对象选择
            selected_objects = validate_object_selection(context, min_count=1, obj_type='MESH')
            
            active_object = context.active_object
            obj_transformation = []
            processed_count = 0
            failed_objects = []
            
            # 更新视图层
            context.view_layer.update()

            # 保存对象变换矩阵
            for obj in selected_objects:
                obj_transformation.append({
                    "obj": obj, 
                    "matrix_world": Matrix(obj.matrix_world)
                })

            # 应用物理变换并移除刚体
            for data in obj_transformation:
                try:
                    obj = bpy.data.objects[data["obj"].name]
                    context.view_layer.objects.active = obj
                    
                    # 应用视觉变换
                    bpy.ops.object.visual_transform_apply()
                    
                    # 移除刚体
                    if obj.rigid_body:
                        bpy.ops.rigidbody.object_remove()
                    
                    # 恢复原始变换矩阵
                    obj.matrix_world = data["matrix_world"]
                    processed_count += 1
                    
                except Exception as e:
                    failed_objects.append(f"{data['obj'].name}: {str(e)}")

            # 恢复活动对象
            context.view_layer.objects.active = active_object
            
            # 报告结果
            if processed_count > 0:
                self.report({'INFO'}, f"成功应用物理到 {processed_count} 个对象")
            
            if failed_objects:
                error_msg = "应用物理失败的对象:\n" + "\n".join(failed_objects[:3])
                if len(failed_objects) > 3:
                    error_msg += f"\n... 还有 {len(failed_objects) - 3} 个对象失败"
                self.report({'WARNING'}, error_msg)

            return {'FINISHED'}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"应用物理失败: {str(e)}")
            return {'CANCELLED'}


classes = (
    PhysicsCalculateOperator,
    PhysicsAddActiveOperator,
    PhysicsApplyOperator,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 