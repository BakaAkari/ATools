import bpy
from bpy.utils import register_class, unregister_class
from ..i18n.translation import get_text
from ..config.constants import UIConstants


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
        header, physics_panel = layout.panel("physics_panel", default_closed=False)
        header.label(text="Physics")
        if physics_panel:
            physics_box = physics_panel.box()
            physics_column = physics_box.column()
            physics_column.prop(wm.quick_physics, 'physics_friction', text=get_text("Friction", context), slider=True)
            physics_column.prop(wm.quick_physics, 'physics_time_scale', text=get_text("Time Scale", context))
            if not wm.quick_physics.running_physics_calculation:
                physics_column.operator('physics.calculate', text=get_text("开始模拟", context))
            else:
                physics_column.prop(wm.quick_physics, 'running_physics_calculation', text=get_text("Cancel Calculation", context), icon="X")

        # 3. Export to engine 导出面板
        header, export_panel = layout.panel("export_panel", default_closed=False)
        header.label(text="Export to engine")
        if export_panel:
            export_box = export_panel.box()
            export_column = export_box.column()
            export_column.prop(props, 'export_rule', text=get_text("Export Rule", context))
            export_column.prop(props, 'exportpath', text=get_text("Export Location", context))
            export_column.operator('export.fbx_batch', text=get_text("Export Object", context))


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