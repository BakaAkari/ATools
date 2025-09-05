import os
import bpy
from bpy.utils import register_class, unregister_class
from ..config.constants import PreferenceSettings, MaterialNodes
from ..utils.common_utils import ATOperationError, validate_object_selection, get_active_material_nodes
import bmesh


class MeshResizeOperator(bpy.types.Operator):
    """根据纹理尺寸调整网格大小"""
    bl_idname = "mesh.resize_to_texture"
    bl_label = "Resize Size Mesh"

    def execute(self, context):
        try:
            # 验证对象选择
            selected_objs = validate_object_selection(context, min_count=1, obj_type='MESH')
            resized_count = 0
            failed_objects = []

            for obj in selected_objs:
                try:
                    self._resize_mesh_to_texture(obj)
                    resized_count += 1
                except Exception as e:
                    failed_objects.append(f"{obj.name}: {str(e)}")

            # 报告结果
            if resized_count > 0:
                self.report({'INFO'}, f"成功调整 {resized_count} 个网格大小")
            
            if failed_objects:
                error_msg = "调整失败的对象:\n" + "\n".join(failed_objects[:3])
                if len(failed_objects) > 3:
                    error_msg += f"\n... 还有 {len(failed_objects) - 3} 个对象失败"
                self.report({'WARNING'}, error_msg)
                
            return {'FINISHED'}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"调整网格大小失败: {str(e)}")
            return {'CANCELLED'}
    
    def _resize_mesh_to_texture(self, obj):
        """根据纹理大小调整网格尺寸"""
        # 验证对象有材质
        if not obj.active_material:
            raise ATOperationError(f"对象 {obj.name} 没有活动材质")
        
        # 获取材质节点
        nodes = get_active_material_nodes(obj)
        
        # 查找纹理图像节点
        texture_image = None
        for node in nodes:
            if node.type == MaterialNodes.TEX_IMAGE and node.image:
                texture_image = node.image
                break
        
        if not texture_image:
            raise ATOperationError(f"对象 {obj.name} 的材质中未找到有效的纹理图像")
        
        # 获取图像尺寸并转换为世界单位
        image_width = texture_image.size[0] * 0.001  # 转换为米
        image_height = texture_image.size[1] * 0.001
        
        print(f"调整 {obj.name}: 图像尺寸 {texture_image.size[0]}x{texture_image.size[1]}")
        
        # 验证网格有足够的顶点（至少4个顶点用于平面）
        if len(obj.data.vertices) < 4:
            raise ATOperationError(f"对象 {obj.name} 的顶点数量不足（需要至少4个顶点）")
        
        # 调整前4个顶点的位置（假设是平面网格）
        vertices = obj.data.vertices
        
        # 设置四个角的坐标
        vertices[0].co = (-image_width, -image_height, 0)  # 左下
        vertices[1].co = (image_width, -image_height, 0)   # 右下
        vertices[2].co = (-image_width, image_height, 0)   # 左上
        vertices[3].co = (image_width, image_height, 0)    # 右上
        
        # 更新网格
        obj.data.update()


class MeshRenameOperator(bpy.types.Operator):
    """基于集合名称重命名网格对象"""
    bl_idname = "mesh.rename_by_collection"
    bl_label = "Rename"

    def execute(self, context):
        try:
            act_obj = context.active_object
            
            if not act_obj:
                self.report({'ERROR'}, "没有活动对象")
                return {'CANCELLED'}
            
            if not act_obj.users_collection:
                self.report({'ERROR'}, "活动对象不属于任何集合")
                return {'CANCELLED'}
            
            # 获取对象所在的集合
            collection = act_obj.users_collection[0]
            collection_name = collection.name
            
            # 获取集合中的所有网格对象
            mesh_objects = [obj for obj in collection.all_objects if obj.type == 'MESH']
            
            if not mesh_objects:
                self.report({'WARNING'}, f"集合 '{collection_name}' 中没有网格对象")
                return {'FINISHED'}
            
            renamed_count = 0
            failed_renames = []
            mesh_count = len(mesh_objects)
            
            # 重命名网格对象
            for i, obj in enumerate(mesh_objects):
                try:
                    self._rename_object_and_mesh(obj, collection_name, i + 1, mesh_count)
                    renamed_count += 1
                except Exception as e:
                    failed_renames.append(f"{obj.name}: {str(e)}")
            
            # 报告结果
            if renamed_count > 0:
                self.report({'INFO'}, f"成功重命名 {renamed_count} 个对象 (基于集合: {collection_name})")
            
            if failed_renames:
                error_msg = "重命名失败的对象:\n" + "\n".join(failed_renames[:3])
                if len(failed_renames) > 3:
                    error_msg += f"\n... 还有 {len(failed_renames) - 3} 个对象失败"
                self.report({'WARNING'}, error_msg)
                
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"重命名操作失败: {str(e)}")
            return {'CANCELLED'}
    
    def _rename_object_and_mesh(self, obj, collection_name, index, total_count):
        """重命名对象和其网格数据"""
        # 根据对象数量决定是否添加后缀
        if total_count == 1:
            # 只有一个对象时，直接使用集合名称
            new_name = collection_name
        else:
            # 多个对象时，添加序号后缀
            new_name = f"{collection_name}_{str(index).zfill(2)}"
        
        # 重命名对象
        old_obj_name = obj.name
        obj.name = new_name
        
        # 重命名网格数据
        if obj.data:
            obj.data.name = new_name
            print(f"重命名: {old_obj_name} -> {new_name}")
        
        # 处理UV通道
        self._process_uv_channels(obj)
    
    def _process_uv_channels(self, obj):
        """处理对象的UV通道，根据UV通道数量重命名为UVMap_01, UVMap_02等"""
        mesh = obj.data
        uv_layers = mesh.uv_layers
        
        # 检查对象是否存在UV通道
        if not uv_layers:
            # 不存在UV通道，新建一个
            new_uv = uv_layers.new(name="UVMap_01")
            print(f"为 {obj.name} 创建新的UV通道: UVMap_01")
        else:
            # 存在UV通道，根据数量重命名所有UV通道
            uv_count = len(uv_layers)
            for i, uv_layer in enumerate(uv_layers):
                expected_name = f"UVMap_{str(i + 1).zfill(2)}"
                if uv_layer.name != expected_name:
                    uv_layer.name = expected_name
                    print(f"将 {obj.name} 的UV通道{i}重命名为{expected_name}")
                else:
                    print(f"{obj.name} 的UV通道{i}已经是{expected_name}，无需修改")


class MeshCleanOperator(bpy.types.Operator):
    """清理网格对象属性"""
    bl_idname = "mesh.clean_attributes"
    bl_label = "初始化模型信息"

    def execute(self, context):
        try:
            # 验证对象选择
            selected_objects = validate_object_selection(context, min_count=1, obj_type='MESH')
            processed_count = 0
            failed_objects = []
            
            for obj in selected_objects:
                try:
                    self._clean_object(context, obj)
                    processed_count += 1
                except Exception as e:
                    failed_objects.append(f"{obj.name}: {str(e)}")
                    
            # 报告结果
            if processed_count > 0:
                self.report({'INFO'}, f"成功处理 {processed_count} 个对象")
            
            if failed_objects:
                error_msg = "处理失败的对象:\n" + "\n".join(failed_objects[:3])  # 只显示前3个错误
                if len(failed_objects) > 3:
                    error_msg += f"\n... 还有 {len(failed_objects) - 3} 个对象失败"
                self.report({'WARNING'}, error_msg)
            
            if processed_count == 0 and not failed_objects:
                self.report({'WARNING'}, "没有处理任何对象")
                
            return {'FINISHED'}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"清理对象失败: {str(e)}")
            return {'CANCELLED'}
    
    def _clean_object(self, context, obj):
        """清理单个对象"""
        # 设置为活动对象
        context.view_layer.objects.active = obj
        
        # 进入编辑模式
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        
        # 清除边属性
        bpy.ops.transform.edge_crease(value=-1)
        bpy.ops.transform.edge_bevelweight(value=-1)
        bpy.ops.mesh.mark_sharp(clear=True)
        
        # 退出编辑模式
        bpy.ops.object.editmode_toggle()
        
        # 处理自定义分割法线
        try:
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
        except:
            bpy.ops.mesh.customdata_custom_splitnormals_add()
        
        # 重新进入编辑模式处理缝合边
        bpy.ops.object.editmode_toggle()
        
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        
        # 为缝合边添加硬边标记
        for edge in bm.edges:
            if edge.seam:
                bpy.ops.mesh.select_all(action='DESELECT')
                edge.select = True
                bpy.ops.mesh.mark_sharp()
        
        # 更新网格并退出编辑模式
        bmesh.update_edit_mesh(mesh)
        bpy.ops.object.editmode_toggle()


class MeshResetOriginOperator(bpy.types.Operator):
    """重置网格原点"""
    bl_idname = "mesh.reset_origin"
    bl_label = "Reset Origin"

    def execute(self, context):
        selobj = bpy.context.selected_objects
        for i in selobj:
            bpy.context.view_layer.objects.active = i
            print(bpy.data.objects[i.name_full].dimensions.z)
        return {'FINISHED'}


classes = (
    MeshResizeOperator,
    MeshRenameOperator,
    MeshCleanOperator,
    MeshResetOriginOperator,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 