import os
import bpy
from bpy.utils import register_class, unregister_class
from .ATFunctions import *
import bmesh

class OptiEVRenderOperator(bpy.types.Operator):
    bl_idname = "object.optievrender"
    bl_label = "最优EV设置"

    def execute(self, context):
        actobj: bpy.types.Object

        actobj = bpy.context.active_object
        actmat = actobj.active_material
        act_scene = bpy.context.window.scene
        # 设置eevee参数
        bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
        # 设置渲染参数
        bpy.data.scenes[act_scene.name].eevee.taa_samples = 0
        bpy.data.scenes[act_scene.name].eevee.taa_render_samples = 512
        #AO
        bpy.context.scene.eevee.use_gtao = True
        bpy.context.scene.eevee.gtao_quality = 1
        #光线追踪
        bpy.context.scene.eevee.use_raytracing = True
        #体积
        bpy.context.scene.eevee.volumetric_tile_size = '4'
        bpy.context.scene.eevee.volumetric_sample_distribution = 1
        bpy.context.scene.eevee.use_volumetric_shadows = True
        bpy.context.scene.eevee.volumetric_shadow_samples = 64
        #阴影
        bpy.context.scene.eevee.shadow_ray_count = 3
        #高品质法线
        bpy.context.scene.render.use_high_quality_normals = True
        #色彩管理
        bpy.context.scene.view_settings.look = 'AgX - High Contrast'
        bpy.context.scene.render.image_settings.compression = 0

        return {'FINISHED'}


class OptiCYRenderOperator(bpy.types.Operator):
    bl_idname = "object.opticyrender"
    bl_label = "最优CY设置"

    def execute(self, context):
        actobj: bpy.types.Object

        actobj = bpy.context.active_object
        actmat = actobj.active_material
        act_scene = bpy.context.window.scene
        # 设置cycles参数
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.data.scenes[act_scene.name].cycles.feature_set = 'EXPERIMENTAL'
        bpy.data.scenes["Scene"].cycles.device = 'GPU'
        # 设置渲染参数
        bpy.context.scene.cycles.preview_adaptive_threshold = 0.01
        bpy.context.scene.cycles.use_preview_denoising = True
        bpy.context.scene.cycles.tile_size = 512
        bpy.context.scene.view_settings.look = 'AgX - High Contrast'
        bpy.context.scene.render.image_settings.compression = 0

        return {'FINISHED'}

class Resize_Mesh_Operator(bpy.types.Operator):
    bl_idname = "object.resizemesh"
    bl_label = "Resize Size Mesh"

    def execute(self, context):
        sel_objs = bpy.context.selected_objects
        for obj in sel_objs:
            mat_nodes = obj.active_material.node_tree.nodes
            for node in mat_nodes:
                if node.type == 'TEX_IMAGE':
                    print(node.image.size[0])
                    image_x = node.image.size[0] * 0.001
                    image_y = node.image.size[1] * 0.001

            obj.data.vertices[0].co[0] = image_x * -1
            obj.data.vertices[1].co[0] = image_x
            obj.data.vertices[2].co[0] = image_x * -1
            obj.data.vertices[3].co[0] = image_x

            obj.data.vertices[0].co[1] = image_y * -1
            obj.data.vertices[1].co[1] = image_y * -1
            obj.data.vertices[2].co[1] = image_y
            obj.data.vertices[3].co[1] = image_y
        return {'FINISHED'}


class Rename_Operator(bpy.types.Operator):
    bl_idname = "object.rename"
    bl_label = "Rename"

    def execute(self, context):
        obj: bpy.types.Object

        sel_objs = bpy.context.selected_objects
        act_obj = bpy.context.active_object
        collname = bpy.context.collection.name

        for i, obj in enumerate(bpy.data.collections[act_obj.users_collection[0].name].all_objects):
            if obj.type == 'MESH':
                obj.name = bpy.data.collections[obj.users_collection[0].name].name + '_' + str(i + 1).zfill(2)
                bpy.data.meshes[obj.to_mesh().name].name = bpy.data.collections[obj.users_collection[0].name].name + '_' + str(i + 1).zfill(2)
        return {'FINISHED'}


class CleanObjectOperator(bpy.types.Operator):
    bl_idname = "object.cleanobject"
    bl_label = "初始化模型信息"

    def execute(self, context):
        selection = bpy.context.selected_objects
        processed_count = 0
        for o in selection:
            try:
                bpy.context.view_layer.objects.active = o
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='SELECT')
                
                # 清除所有边的 edge_crease
                bpy.ops.transform.edge_crease(value=-1)
                
                # 清除所有边的 edge_bevelweight
                bpy.ops.transform.edge_bevelweight(value=-1)
                
                # 清除所有硬边
                bpy.ops.mesh.mark_sharp(clear=True)
                
                bpy.ops.object.editmode_toggle()
                
                # 尝试清除自定义分割法线，如果失败则添加自定义分割法线
                try:
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
                except:
                    self.report({'INFO'}, f"对象 {o.name} 没有自定义分割法线，正在添加...")
                    bpy.ops.mesh.customdata_custom_splitnormals_add()
                
                # 重新进入编辑模式
                bpy.ops.object.editmode_toggle()
                
                # 获取当前网格数据
                mesh = o.data
                bm = bmesh.from_edit_mesh(mesh)
                
                # 遍历所有边，为缝合边添加硬边标记
                for edge in bm.edges:
                    if edge.seam:
                        # 清除所有选择
                        bpy.ops.mesh.select_all(action='DESELECT')
                        # 选择当前缝合边
                        edge.select = True
                        # 标记选中的边为硬边
                        bpy.ops.mesh.mark_sharp()
                
                # 更新网格
                bmesh.update_edit_mesh(mesh)
                
                bpy.ops.object.editmode_toggle()
                processed_count += 1

            except Exception as e:
                self.report({'ERROR'}, f"处理对象 {o.name} 时出错: {str(e)}")
                print(f"Error processing object {o.name}: {str(e)}")
        
        if processed_count > 0:
            self.report({'INFO'}, f"成功处理 {processed_count} 个对象")
        else:
            self.report({'WARNING'}, "没有处理任何对象")
            
        return {'FINISHED'}


class ReSetOriginOperator(bpy.types.Operator):
    bl_idname = "object.resetorigin"
    bl_label = "Reset Origin"

    def execute(self, context):
        selobj = bpy.context.selected_objects
        for i in selobj:
            bpy.context.view_layer.objects.active = i
            print(bpy.data.objects[i.name_full].dimensions.z)
        return {'FINISHED'}


#===========================================================================================================

class Translation(bpy.types.Operator):
    bl_idname = "object.translation"
    bl_label = "切换中英文"

    def execute(self, context):
        viewlanguage = context.preferences.view.language
        prefview = context.preferences.view
        if viewlanguage != "en_US":
            context.preferences.view.language = "en_US"
        else:
            try:
                context.preferences.view.language = "zh_CN"
            except:
                context.preferences.view.language = "zh_HANS"
            prefview.use_translate_new_dataname = False
        return {'FINISHED'}


#===========================================================================================================
class ExportFBX(bpy.types.Operator):
    bl_idname = "object.exportfbx"
    bl_label = "导出FBX"

    def execute(self, context):
        wm = context.window_manager
        props = wm.atprops
        exportpath = props.exportpath
        absexportpath = bpy.path.abspath(exportpath)
        selected_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

        if selected_objs is None:
            print("没有选中的对象！")
            return

        for obj in selected_objs:
            file_name = obj.name + ".fbx"
            output_path = os.path.join(absexportpath, file_name)

            output_path = os.path.normpath(output_path)
            output_dir_path = os.path.dirname(output_path)
            if not os.path.exists(output_dir_path):
                os.makedirs(output_dir_path)

            objects_to_export = [obj]
            if obj.children:
                for child in obj.children:
                    if child.parent == obj and child.type == 'MESH':
                        objects_to_export.append(child)

            bpy.ops.object.select_all(action='DESELECT')
            for obj_to_export in objects_to_export:
                obj_to_export.select_set(True)

            if props.export_rule == 'UNREAL':
                bpy.ops.export_scene.fbx(filepath=output_path, use_selection=True, use_space_transform=True, bake_space_transform=True, axis_forward='-Z', axis_up='Y')
            elif props.export_rule == 'UNITY':
                bpy.ops.export_scene.fbx(filepath=output_path, use_selection=True, use_space_transform=True, bake_space_transform=True, axis_forward='X', axis_up='Y')
            print(f"导出成功: {output_path}")

        return {'FINISHED'}


#===========================================================================================================
class Setstartframe(bpy.types.Operator):
    bl_idname = "object.setstartframe"
    bl_label = "SetStartFrame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        try:
            pass  # Set Start Frame Script Start
            import bpy
            actscene = bpy.context.scene
            bpy.data.scenes[actscene.name].frame_start = bpy.data.scenes[actscene.name].frame_current
            pass  # Set Start Frame Script End
        except Exception as exc:
            print(str(exc) + " | Error in execute function of SetStartFrame")
        return {"FINISHED"}

    def invoke(self, context, event):
        try:
            pass
        except Exception as exc:
            print(str(exc) + " | Error in invoke function of SetStartFrame")
        return self.execute(context)


class Setendframe(bpy.types.Operator):
    bl_idname = "object.setendframe"
    bl_label = "SetEndFrame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        try:
            pass  # Set End Frame Script Start
            import bpy
            actscene = bpy.context.scene
            bpy.data.scenes[actscene.name].frame_end = bpy.data.scenes[actscene.name].frame_current
            pass  # Set End Frame Script End
        except Exception as exc:
            print(str(exc) + " | Error in execute function of SetEndFrame")
        return {"FINISHED"}

    def invoke(self, context, event):
        try:
            pass
        except Exception as exc:
            print(str(exc) + " | Error in invoke function of SetEndFrame")
        return self.execute(context)


class StopLoop_OP(bpy.types.Operator):
    bl_idname = "object.stoploop"
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
    
#===========================================================================================================
classes = (
    OptiEVRenderOperator,
    OptiCYRenderOperator,
    Resize_Mesh_Operator,
    Rename_Operator,
    CleanObjectOperator,
    ReSetOriginOperator,
    Translation,
    Setstartframe,
    Setendframe,
    StopLoop_OP,
    ExportFBX,
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
