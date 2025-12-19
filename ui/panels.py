import bpy
from bpy.utils import register_class, unregister_class
from ..i18n.translation import get_text
from ..config.constants import UIConstants


class AT_UL_CustomColliderList(bpy.types.UIList):
    """自定义碰撞体列表绘制类"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # item 是 CustomColliderItem 实例
        if item.obj:
            layout.label(text=item.obj.name, icon='OBJECT_DATAMODE')
        else:
            layout.label(text="<Missing Object>", icon='ERROR')


class MainPanel(bpy.types.Panel):
    """主面板"""
    bl_idname = "VIEW3D_PT_atools_main"
    bl_label = "Akari Tool Bag"
    bl_category = UIConstants.PANEL_CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = UIConstants.PANEL_ORDER_MAIN

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        wm = context.window_manager
        props = wm.atprops
        
        layout = self.layout

        # 1. Operator 操作面板 (2*2布局)
        header, operator_panel = layout.panel("operator_panel", default_closed=False)
        header.label(text="Operator")
        if operator_panel:
            operator_box = operator_panel.box()
            operator_column = operator_box.column()
            
            # 第一行：重命名对象 和 清理对象
            row1 = operator_column.row()
            row1.operator('mesh.rename_by_collection', text=get_text("Rename Object", context))
            row1.operator('mesh.clean_attributes', text=get_text("Clean Object", context))
            
            # 第二行：重载图像 和 调整网格
            row2 = operator_column.row()
            row2.operator('image.reload_all', text=get_text("Reload Images", context))
            row2.operator('mesh.resize_to_texture', text=get_text("Resize Mesh", context))

        # 2. Physics 物理面板
        header, physics_panel = layout.panel("physics_panel", default_closed=True)
        header.label(text="Physics")
        if physics_panel:
            physics_box = physics_panel.box()
            physics_column = physics_box.column()
            physics_column.prop(wm.atprops, 'physics_collision_shape', text="Collision Shape")
            physics_column.prop(wm.atprops, 'physics_collision_margin', text="Collision Margin", slider=True)
            physics_column.prop(wm.atprops, 'physics_friction', text=get_text("Friction", context), slider=True)
            physics_column.prop(wm.atprops, 'physics_time_scale', text=get_text("Time Scale", context))
            physics_column.prop(wm.atprops, 'physics_solver_iterations', text=get_text("Solver Iterations", context))
            physics_column.prop(wm.atprops, 'physics_split_impulse', text=get_text("Split Impulse", context))
            physics_column.prop(wm.atprops, 'physics_restitution', text=get_text("Restitution", context), slider=True)
            
            # Custom Colliders
            physics_column.separator()
            physics_column.prop(wm.atprops, 'physics_use_custom_colliders', text="Use Custom Colliders")
            if wm.atprops.physics_use_custom_colliders:
                box = physics_column.box()
                row = box.row()
                row.template_list("AT_UL_CustomColliderList", "custom_colliders", wm.atprops, "physics_custom_colliders", wm.atprops, "physics_custom_collider_index", rows=3)
                
                col = row.column(align=True)
                col.operator("physics.remove_custom_collider", icon='REMOVE', text="")
                
                row = box.row(align=True)
                row.operator("physics.get_custom_colliders", text="Get Selected")
                row.operator("physics.clear_custom_colliders", text="Clear List")
            
            physics_column.separator()

            if not wm.atprops.running_physics_calculation:
                physics_column.operator('physics.calculate', text=get_text("开始模拟", context))
            else:
                physics_column.prop(wm.atprops, 'running_physics_calculation', text=get_text("Cancel Calculation", context), icon="X")

        # 3. Explode 爆炸图面板
        header, explode_panel = layout.panel("explode_panel", default_closed=True)
        header.label(text=get_text("Explode View", context))
        if explode_panel:
            explode_box = explode_panel.box()
            explode_column = explode_box.column()
            
            # 获取爆炸图属性
            explode_props = wm.atprops.explode_props
            
            # 集合选择下拉菜单
            explode_column.prop(explode_props, 'target_collection', text=get_text("Target Collection", context))
            
            # 记录初始位置和重置按钮
            button_row = explode_column.row()
            button_row.operator('explode.record_initial_positions', text=get_text("Record Initial Positions", context), icon='REC')
            button_row.operator('explode.reset_positions', text=get_text("Reset Positions", context), icon='LOOP_BACK')
            
            # 显示是否已记录初始位置
            if explode_props.has_initial_positions:
                explode_column.label(text=get_text("✓ Recorded Initial Positions", context), icon='CHECKMARK')
            else:
                explode_column.label(text=get_text("⚠ Please Record Initial Positions", context), icon='ERROR')
            
            # 偏移值滑条（实时更新）
            explode_column.prop(explode_props, 'explode_offset', text=get_text("Offset Value", context), slider=True)



class NodePanel(bpy.types.Panel):
    """节点编辑器面板"""
    bl_idname = "NODE_PT_atools_node"
    bl_label = "ATools"
    bl_category = UIConstants.PANEL_CATEGORY
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = UIConstants.PANEL_ORDER_NODE
    
    def draw(self, context):
        act_obj: bpy.types.Object
        layout = self.layout
        act_obj = bpy.context.active_object
        
        if not (act_obj and act_obj.active_material):
            return

        # Import Nodes 面板
        header, import_panel = layout.panel("import_nodes_panel", default_closed=False)
        header.label(text="Import Nodes")
        if import_panel:
            import_box = import_panel.box()
            import_column = import_box.column()
            
            # 导入UE PBR节点组按钮
            import_column.operator('node.create_ue_pbr_group', text="导入 UE PBR 节点组")

        # Operator 操作面板
        header, operator_panel = layout.panel("operator_panel", default_closed=False)
        header.label(text="Operator")
        if operator_panel:
            operator_box = operator_panel.box()
            operator_column = operator_box.column()
            
            # 第一行：切换映射方式 和 曲面细分
            row1 = operator_column.row()
            row1.operator('node.toggle_projection', text=get_text("切换映射方式", context))
            row1.operator('node.add_subdivision', text=get_text("开启曲面细分", context))
            
            # 第二行：重载图像 和 调整网格
            row2 = operator_column.row()
            row2.operator('image.reload_all', text=get_text("Reload Images", context))
            row2.operator('mesh.resize_to_texture', text=get_text("Resize Mesh", context))



classes = (
    AT_UL_CustomColliderList,
    MainPanel,
    NodePanel,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 