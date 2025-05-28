import bpy
from mathutils import Matrix

class QuickPhysics_CalcPhysics(bpy.types.Operator):
    bl_idname = "quick_physics.calc_physics"
    bl_label = "Calculate Physics"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def add_passive_bodies(self, context, add):
        quick_physics = context.window_manager.quick_physics
        active_object = context.active_object

        for obj in context.visible_objects:
            if not obj.select_get() and obj.type == "MESH":
                context.view_layer.objects.active = obj
                if add and obj.rigid_body == None:
                    bpy.ops.rigidbody.object_add()
                    obj.rigid_body.friction = quick_physics.physics_friction
                    obj.rigid_body.use_margin = True
                    obj.rigid_body.collision_margin = 0.0001
                    obj.rigid_body.type = "PASSIVE"
                    obj.rigid_body.collision_shape = "MESH"
                elif not add and obj.rigid_body != None:
                    bpy.ops.rigidbody.object_remove()

        context.view_layer.objects.active = canvas = active_object

    def invoke(self, context, event):
        # Initialize variables here instead of in __init__
        self.fps = 0
        self.frame_start = 0
        self.frame_end = 0
        self.frame_current = 0
        self.world_enabled = True
        self.use_split_impulse = True
        self.world_time_scale = 1.0

        mesh_objects = 0
        for obj in context.selected_objects:
            if obj.type == "MESH":
                mesh_objects += 1
                break
        if mesh_objects == 0:
            self.report({'WARNING'}, 'No Objects for Physics selected.')
            return {"CANCELLED"}

        wm = context.window_manager
        quick_physics = context.window_manager.quick_physics
        wm.modal_handler_add(self)
        quick_physics.running_physics_calculation = True

        if context.scene.rigidbody_world == None:
            bpy.ops.rigidbody.world_add()

        self.fps = context.scene.render.fps
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        self.frame_current = context.scene.frame_current
        self.world_enabled = context.scene.rigidbody_world.enabled
        self.use_split_impulse = context.scene.rigidbody_world.use_split_impulse
        self.world_time_scale = context.scene.rigidbody_world.time_scale

        context.scene.rigidbody_world.time_scale = quick_physics.physics_time_scale
        context.scene.render.fps = 24
        context.scene.frame_start = 0
        context.scene.frame_end = 10000
        context.scene.frame_current = 0
        context.scene.rigidbody_world.enabled = True
        context.scene.rigidbody_world.use_split_impulse = True

        self.add_passive_bodies(context, True)

        bpy.ops.object.as_add_active_physics()

        bpy.ops.screen.animation_play()

        tot = context.scene.frame_end
        wm.progress_begin(0, tot)
        return {"RUNNING_MODAL"}

    def exit_modal(self, context, wm):
        quick_physics = context.window_manager.quick_physics
        quick_physics.running_physics_calculation = False
        bpy.ops.screen.animation_play()
        bpy.ops.object.as_apply_physics()
        # bpy.ops.screen.animation_cancel()

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
        wm = context.window_manager
        quick_physics = context.window_manager.quick_physics
        if event.type in {
            "ESC"} or context.scene.frame_current >= 10000 or not quick_physics.running_physics_calculation:
            self.exit_modal(context, wm)
            return {"CANCELLED"}
        wm.progress_update(context.scene.frame_current)
        return {"PASS_THROUGH"}


class QuickPhysics_AddActivePhysics(bpy.types.Operator):
    bl_idname = "object.as_add_active_physics"
    bl_label = "Add physics to Assets"
    bl_description = "Sets up Assets as rigidbody objects."

    def execute(self, context):
        quick_physics = context.window_manager.quick_physics
        active_object = context.active_object
        for obj in context.selected_objects:
            if obj.type == "MESH":
                context.view_layer.objects.active = obj
                bpy.ops.rigidbody.object_add()
                obj.rigid_body.friction = quick_physics.physics_friction
        context.view_layer.objects.active = active_object

        return {'FINISHED'}


class QuickPhysics_ApplyPhysics(bpy.types.Operator):
    bl_idname = "object.as_apply_physics"
    bl_label = "Apply physics to Assets"
    bl_description = "Applies physics to assets and removes rigidbodies."

    def execute(self, context):
        active_object = context.active_object

        obj_transformation = []
        context.view_layer.update()

        for obj in context.selected_objects:
            obj_transformation.append({"obj": obj, "matrix_world": Matrix(obj.matrix_world)})

        for data in obj_transformation:
            obj = bpy.data.objects[data["obj"].name]

            context.view_layer.objects.active = obj
            bpy.ops.object.visual_transform_apply()
            bpy.ops.rigidbody.object_remove()

            obj.matrix_world = data["matrix_world"]

        context.view_layer.objects.active = active_object

        return {'FINISHED'}


class QuickPhysicsPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_QuickPhysics"
    bl_label = "Quick Physics"
    bl_category = "Tool"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 81

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        header, physics = layout.panel("physics_panel", default_closed=False)
        header.label(text="Quick Physics")
        if physics:
            row = physics.row()
            physics_box = row.box()
            physics_column = physics_box.column()
            physics_column.label(text='Quick Physics')
            physics_column.prop(wm.quick_physics, 'physics_friction', text="Friction", slider=True)
            physics_column.prop(wm.quick_physics, 'physics_time_scale', text="Time Scale")
            if not wm.quick_physics.running_physics_calculation:
                physics_column.operator('quick_physics.calc_physics', text="开始模拟")
            else:
                physics_column.prop(wm.quick_physics, 'running_physics_calculation', text="Cancel Calculation", icon="X")

classes = (
    QuickPhysics_CalcPhysics,
    QuickPhysics_AddActivePhysics,
    QuickPhysics_ApplyPhysics,
    QuickPhysicsPanel,
)

def register():
    global classes
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    global classes
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register() 