import bpy
from bpy.utils import register_class, unregister_class
from .ATFunctions import *
from .ATOperator3D import *
from .ATUtils import is_pil_available


class AtPanel3D(bpy.types.Panel):
    bl_idname = "OBJECT_PT_AT"
    bl_label = "Akari Tool Bag"
    bl_category = "Tool"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 80

    
    # bl_options = {'DEFAULT_CLOSED'}
    

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw_header(self, context):
        self.layout.label(text="", icon='DOT')

    def draw(self, context):
        wm = context.window_manager
        props = wm.atprops
        
        layout = self.layout

        # 添加PIL状态显示
        if not is_pil_available():
            box = layout.box()
            box.label(text="PIL library is not installed", icon='ERROR')
            box.operator('object.atinstallpil', text='Install PIL')

        # layout.operator("object.at3dtestoperator", text="Test Operator")

        header, render = layout.panel("render_panel", default_closed=False)
        header.label(text="Render Settings")
        if render:
            render_box = render.box()
            render_column = render_box.column()
            render_row = render_column.row()
            render_row.operator('object.optievrender', text="EEVEE Best")
            render_row.operator('object.opticyrender', text="Cycles Best")

        header, export = layout.panel("export_panel", default_closed=False)
        header.label(text="Game Engine Operator")
        if export:
            export_box = export.box()
            export_column = export_box.column()
            export_column.prop(props, 'export_rule', text="Export Rule")
            export_column.prop(props, 'exportpath', text="Export Location")
            export_column.operator('object.exportfbx', text='Export Object')

        header, object = layout.panel("object_panel", default_closed=False)
        header.label(text="Object Operator")
        if object:
            object_box = object.box()
            object_column = object_box.column()
            object_column.label(text='Object Operator')
            object_column.operator('object.rename', text='Rename Object')
            # object_column.operator('object.resetorigin', text='Reset Origin')
            object_column.operator('object.cleanobject', text='Clean Object')

        header, image = layout.panel("image_panel", default_closed=False)
        header.label(text="image Operator")
        if image:
            image_box = image.box()
            image_column = image_box.column()
            image_row = image_column.row()
            image_column.label(text='Image Operator')
            image_column.operator('object.reloadimage', text='Reload Images')
            image_column.operator('object.resizemesh', text='Resize Mesh')

class AtPanelNode(bpy.types.Panel):
    bl_idname = "OBJECT_PT_FixBridgeTools"
    bl_label = "Fix Bridge Tools"
    bl_category = "Tool"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 15

    # bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        self.layout.label(text="", icon='DOT')
    
    def draw(self, context):
        act_obj: bpy.types.Object
        wm = context.window_manager

        layout = self.layout
        act_obj = bpy.context.active_object
        nodes = None
        
        if act_obj and act_obj.active_material:
            try:
                nodes = act_obj.active_material.node_tree.nodes
            except:
                nodes = None
        else:
            return

        header, image = layout.panel("AT_panel", default_closed=False)
        header.label(text="AT Operator")
        if image:
            image_box = image.box()
            image_column = image_box.column()
            image_row = image_column.row()
            image_row.operator('object.changeprojection', text="切换映射方式")
            image_row.operator('object.addsubd', text="开启曲面细分")

        
        header, image = layout.panel("image_panel", default_closed=False)
        header.label(text="image Operator")
        if image:
            image_box = image.box()
            image_column = image_box.column()
            image_row = image_column.row()
            image_row.operator('object.reloadimage', text='Reload Images')
            image_row.operator('object.resizemesh', text='Resize Mesh')
            second_row = image_column.row()


        try:
            if act_obj.active_material and nodes['Tiling Scale']:
                header, bridge = layout.panel("bridge_panel", default_closed=False)
                header.label(text="Bridge Operator")
                if bridge:
                    bridge_box = bridge.box()
                    bridge_column = bridge_box.column()
                    bridge_row = bridge_column.row()
                    bridge_column.prop(nodes['Tiling Scale'].outputs['Value'], "default_value", text='Tiling Scale')
                    bridge_column.prop(nodes['Bump Strength'].outputs['Value'], "default_value", text='Bump Strength')
        except:
            pass
        
        try:
            header, orm = layout.panel("merge_panel", default_closed=True)
            header.label(text="ORM Workflow")
            if orm:
                header, bridge_merge = orm.panel("brige_merge_panel", default_closed=True)
                header.label(text="Quixel Bridge")
                if bridge_merge:
                    bridge_merge.operator('object.mergebridgetex')
                    
                header, manual_merge = orm.panel("manual_merge_panel", default_closed=True)
                header.label(text="Manual Merge Texture")
                
                if manual_merge:
                    manual_row = manual_merge.row(align=True)
                    op_box = manual_row.box()
                    op_box.scale_x = 1
                    
                    op_box_col_r = op_box.row(align=True)
                    op_box_col_r.operator('object.markcoltex')
                    op_box_col_r.operator('object.delcoltex', icon='X')
                    op_box_opa_r = op_box.row(align=True)
                    op_box_opa_r.operator('object.markopatex')
                    op_box_opa_r.operator('object.delopatex', icon='X')
                    op_box_rough_r = op_box.row(align=True)
                    op_box_rough_r.operator('object.markroughtex')
                    op_box_rough_r.operator('object.delroughtex', icon='X')
                    op_box_metal_r = op_box.row(align=True)
                    op_box_metal_r.operator('object.markmetaltex')
                    op_box_metal_r.operator('object.delmetaltex', icon='X')
                    op_box_ao_r = op_box.row(align=True)
                    op_box_ao_r.operator('object.markaotex')
                    op_box_ao_r.operator('object.delaotex', icon='X')
                    op_box_nor_r = op_box.row(align=True)
                    op_box_nor_r.operator('object.marknortex')
                    op_box_nor_r.operator('object.delnortex', icon='X')
                    
                    label_box = manual_row.box()
                    label_box.scale_x = 1.3
                    
                    label_box.label(text=wm.atprops.col_tex_name)
                    label_box.label(text=wm.atprops.opa_tex_name)
                    label_box.label(text=wm.atprops.rough_tex_name)
                    label_box.label(text=wm.atprops.metal_tex_name)
                    label_box.label(text=wm.atprops.ao_tex_name)
                    label_box.label(text=wm.atprops.nor_tex_name)
                    #合并贴图
                    manual_merge.operator('object.manualmergetex')
                    manual_merge.operator('object.checktexturename')
        except:
            pass
        # layout.operator('object.attestoperator', text="测试按钮")

classes = (
    AtPanel3D,
    AtPanelNode,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
