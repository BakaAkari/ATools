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

        # ATex 面板
        header, atex_panel = layout.panel("atex_panel", default_closed=False)
        header.label(text="ATex")
        if atex_panel:
            atex_box = atex_panel.box()
            atex_column = atex_box.column()
            
            # 获取ATex属性
            wm = context.window_manager
            atex_props = wm.atex_props
            
            # 检查是否启用ATex功能
            if not atex_props.enable_atex:
                atex_column.label(text="请在偏好设置中启用ATex功能")
                return
            
            # 8个节点拾取按钮
            node_props = [
                ('col_node', "Col"),
                ('roug_node', "Roug"),
                ('meta_node', "Meta"),
                ('nor_node', "Nor"),
                ('ao_node', "AO"),
                ('opa_node', "Opa"),
                ('emic_node', "EmiC"),
                ('emia_node', "EmiA")
            ]
            
            for prop_name, label in node_props:
                row = atex_column.row()
                # 拾取节点按钮 - 宽度缩窄一倍
                op = row.operator('atex.pick_node', text=label)
                op.node_property = prop_name
                row.scale_x = 5
                
                # 显示贴图名称
                node_name = getattr(atex_props, prop_name)
                if node_name:
                    # 尝试获取节点和贴图名称
                    if context.active_object and context.active_object.active_material:
                        node_tree = context.active_object.active_material.node_tree
                        if node_tree and node_name in node_tree.nodes:
                            node = node_tree.nodes[node_name]
                            if node.type == 'TEX_IMAGE' and node.image:
                                row.label(text=node.image.name)
                            else:
                                row.label(text="节点无效")
                        else:
                            row.label(text="节点不存在")
                    else:
                        row.label(text="节点不存在")
                else:
                    row.label(text="未选择")
            
            # 输出路径
            atex_column.prop(atex_props, 'output_path', text="输出路径")
            
            # 资产名输入栏
            atex_column.prop(atex_props, 'asset_name', text="资产名")
            
            # 导出合并贴图按钮
            atex_column.operator('atex.merge_textures', text="导出合并贴图")
            
            # 创建材质按钮
            atex_column.operator('atex.create_material', text="创建材质")

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