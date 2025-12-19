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


def add_shrink_modifier(obj, strength):
    """添加或更新收缩/膨胀修改器"""
    mod_name = "AT_Physics_Shrink"
    mod = obj.modifiers.get(mod_name)
    if not mod:
        mod = obj.modifiers.new(name=mod_name, type='DISPLACE')
    
    mod.strength = strength
    mod.mid_level = 0.0  # 确保从表面开始偏移
    # 确保修改器在最上层（或合适位置），通常物理计算取最终结果，所以只要开启即可
    # 为了确保效果，可以考虑移到最前？但通常保持默认添加顺序即可，除非有Subsurf
    return mod


def remove_shrink_modifier(obj):
    """移除收缩/膨胀修改器"""
    mod_name = "AT_Physics_Shrink"
    mod = obj.modifiers.get(mod_name)
    if mod:
        obj.modifiers.remove(mod)


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

        objects_to_process = []
        if atprops.physics_use_custom_colliders:
            # Use custom colliders
            for item in atprops.physics_custom_colliders:
                if item.obj:  # Ensure object is valid
                    objects_to_process.append(item.obj)
        else:
            # Use visible objects that are not selected
            objects_to_process = [obj for obj in context.visible_objects if not obj.select_get() and obj.type == "MESH"]

        for obj in objects_to_process:
            context.view_layer.objects.active = obj
            if add and obj.rigid_body == None:
                bpy.ops.rigidbody.object_add()
                obj.rigid_body.friction = atprops.physics_friction
                obj.rigid_body.use_margin = True
                
                # 使用 Displace 修改器来处理 Margin (收缩/膨胀)
                safety_margin = 0.001
                target_margin = atprops.physics_collision_margin
                
                physics_margin = safety_margin
                displace_strength = target_margin - physics_margin
                
                add_shrink_modifier(obj, displace_strength)
                
                obj.rigid_body.collision_margin = physics_margin
                obj.rigid_body.restitution = atprops.physics_restitution
                obj.rigid_body.type = "PASSIVE"
                obj.rigid_body.collision_shape = atprops.physics_collision_shape
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
            self.solver_iterations = PhysicsSettings.DEFAULT_SOLVER_ITERATIONS

            wm = context.window_manager
            atprops = get_atprops(context)
            wm.modal_handler_add(self)
            atprops.running_physics_calculation = True
            
            # Handle selection for custom colliders
            self.deselected_objects = []
            if atprops.physics_use_custom_colliders:
                for item in atprops.physics_custom_colliders:
                    if item.obj and item.obj.select_get():
                        item.obj.select_set(False)
                        self.deselected_objects.append(item.obj)

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
            self.solver_iterations = scene.rigidbody_world.solver_iterations

            # 应用物理模拟设置
            scene.rigidbody_world.time_scale = atprops.physics_time_scale
            scene.render.fps = PhysicsSettings.DEFAULT_FPS
            scene.frame_start = 0
            scene.frame_end = PhysicsSettings.MAX_SIMULATION_FRAMES
            scene.frame_current = 0
            scene.rigidbody_world.enabled = True
            scene.rigidbody_world.use_split_impulse = atprops.physics_split_impulse
            scene.rigidbody_world.solver_iterations = max(1, int(atprops.physics_solver_iterations))

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
        context.scene.rigidbody_world.solver_iterations = self.solver_iterations

        self.add_passive_bodies(context, False)

        # Clean up shrink modifiers from active objects
        # We need to find which objects were active. 
        # Since we don't store the list explicitly in this operator instance (except selection),
        # we can iterate over selection (if selection hasn't changed) or check all visible objects for the modifier.
        # Checking all visible objects is safer and fast enough.
        for obj in context.visible_objects:
            if obj.type == 'MESH':
                 remove_shrink_modifier(obj)

        # Restore selection
        if hasattr(self, 'deselected_objects'):
             for obj in self.deselected_objects:
                 if obj:
                     try:
                         obj.select_set(True)
                     except:
                         pass

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
                    
                    # 使用 Displace 修改器来处理 Margin (收缩/膨胀)
                    # 为了保证物理计算稳定性（特别是Mesh形状），保留一个微小的物理边距
                    safety_margin = 0.001
                    target_margin = atprops.physics_collision_margin
                    
                    # 物理边距设为安全值（不能为负）
                    physics_margin = safety_margin
                    
                    # 修改器偏移 = 目标边距 - 物理边距
                    # 例子: 目标0 -> 物理0.001 -> 偏移 -0.001 -> 最终视觉碰撞面 = 原面
                    displace_strength = target_margin - physics_margin
                    
                    # 总是添加修改器，使用计算后的偏移值
                    add_shrink_modifier(obj, displace_strength)
                    
                    # 将刚体自带的 Margin 设为安全值
                    obj.rigid_body.collision_margin = physics_margin
                    
                    obj.rigid_body.restitution = atprops.physics_restitution
                    # Active objects always use MESH unless we want to expose this too, 
                    # but user asked for "proxy shape of physics objects" which usually refers to passive/colliders in this context.
                    # However, if the user meant "Active" objects too, we can change it here. 
                    # Given the context of optimization, it's usually about the static colliders.
                    # Let's stick to "MESH" for active objects as they need accurate simulation, 
                    # OR we can use the same property if that's what the user intends.
                    # User said "choose proxy shape for physics simulation objects", let's use it for ACTIVE too.
                    # Wait, usually active objects need convex hull or mesh to be useful in simulations like this (debris).
                    # Let's use the property for consistency if that's the request.
                    obj.rigid_body.collision_shape = atprops.physics_collision_shape 
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
                    
                    # Remove shrink modifier BEFORE applying visual transform
                    # (We want the position from the simulation, but the shape from before the shrink)
                    remove_shrink_modifier(obj)
                    
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


class PhysicsGetCustomCollidersOperator(bpy.types.Operator):
    """将选中的Mesh对象添加到自定义碰撞体列表"""
    bl_idname = "physics.get_custom_colliders"
    bl_label = "Get Selected Colliders"
    bl_description = "Add selected mesh objects to custom colliders list"
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
        
    def execute(self, context):
        atprops = get_atprops(context)
        added_count = 0
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Check if already exists
                exists = False
                for item in atprops.physics_custom_colliders:
                    if item.obj == obj:
                        exists = True
                        break
                
                if not exists:
                    item = atprops.physics_custom_colliders.add()
                    item.obj = obj
                    added_count += 1
        
        if added_count > 0:
            self.report({'INFO'}, f"Added {added_count} objects to colliders list")
        else:
            self.report({'WARNING'}, "No new mesh objects added")
            
        return {'FINISHED'}


class PhysicsClearCustomCollidersOperator(bpy.types.Operator):
    """清空自定义碰撞体列表"""
    bl_idname = "physics.clear_custom_colliders"
    bl_label = "Clear Colliders"
    bl_description = "Clear custom colliders list"
    
    def execute(self, context):
        atprops = get_atprops(context)
        atprops.physics_custom_colliders.clear()
        self.report({'INFO'}, "Colliders list cleared")
        return {'FINISHED'}


class PhysicsRemoveCustomColliderOperator(bpy.types.Operator):
    """移除选中的自定义碰撞体"""
    bl_idname = "physics.remove_custom_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove selected collider from list"
    
    @classmethod
    def poll(cls, context):
        atprops = get_atprops(context)
        return len(atprops.physics_custom_colliders) > 0
    
    def execute(self, context):
        atprops = get_atprops(context)
        index = atprops.physics_custom_collider_index
        
        if 0 <= index < len(atprops.physics_custom_colliders):
            atprops.physics_custom_colliders.remove(index)
            if index >= len(atprops.physics_custom_colliders):
                atprops.physics_custom_collider_index = len(atprops.physics_custom_colliders) - 1
                
        return {'FINISHED'}


classes = (
    PhysicsCalculateOperator,
    PhysicsAddActiveOperator,
    PhysicsApplyOperator,
    PhysicsGetCustomCollidersOperator,
    PhysicsClearCustomCollidersOperator,
    PhysicsRemoveCustomColliderOperator,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 