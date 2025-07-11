import os
import bpy
from bpy.utils import register_class, unregister_class
from ..config.constants import ExportSettings
from ..utils.common_utils import ATOperationError, validate_object_selection


class FBXExportOperator(bpy.types.Operator):
    """导出FBX文件"""
    bl_idname = "export.fbx_batch"
    bl_label = "导出FBX"

    def execute(self, context):
        try:
            # 验证对象选择
            selected_objs = validate_object_selection(context, min_count=1, obj_type='MESH')
            
            wm = context.window_manager
            props = wm.atprops
            exportpath = props.exportpath
            
            if not exportpath:
                self.report({'ERROR'}, "请先设置导出路径")
                return {'CANCELLED'}
            
            absexportpath = bpy.path.abspath(exportpath)
            exported_count = 0
            failed_exports = []

            for obj in selected_objs:
                try:
                    self._export_object(obj, absexportpath, props.export_rule)
                    exported_count += 1
                except Exception as e:
                    failed_exports.append(f"{obj.name}: {str(e)}")

            # 报告结果
            if exported_count > 0:
                self.report({'INFO'}, f"成功导出 {exported_count} 个对象")
            
            if failed_exports:
                error_msg = "导出失败的对象:\n" + "\n".join(failed_exports[:3])
                if len(failed_exports) > 3:
                    error_msg += f"\n... 还有 {len(failed_exports) - 3} 个对象失败"
                self.report({'WARNING'}, error_msg)
                
            return {'FINISHED'}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"导出FBX失败: {str(e)}")
            return {'CANCELLED'}
    
    def _export_object(self, obj, export_path, export_rule):
        """导出单个对象"""
        file_name = obj.name + ".fbx"
        output_path = os.path.join(export_path, file_name)
        output_path = os.path.normpath(output_path)
        
        # 确保目录存在
        output_dir_path = os.path.dirname(output_path)
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        # 收集要导出的对象（包括子对象）
        objects_to_export = [obj]
        if obj.children:
            for child in obj.children:
                if child.parent == obj and child.type == 'MESH':
                    objects_to_export.append(child)

        # 选择要导出的对象
        bpy.ops.object.select_all(action='DESELECT')
        for obj_to_export in objects_to_export:
            obj_to_export.select_set(True)

        # 根据导出规则设置参数
        if export_rule == 'UNREAL':
            bpy.ops.export_scene.fbx(
                filepath=output_path, 
                use_selection=True, 
                use_space_transform=True, 
                bake_space_transform=True, 
                axis_forward=ExportSettings.UNREAL_AXIS_FORWARD, 
                axis_up=ExportSettings.UNREAL_AXIS_UP
            )
        elif export_rule == 'UNITY':
            bpy.ops.export_scene.fbx(
                filepath=output_path, 
                use_selection=True, 
                use_space_transform=True, 
                bake_space_transform=True, 
                axis_forward=ExportSettings.UNITY_AXIS_FORWARD, 
                axis_up=ExportSettings.UNITY_AXIS_UP
            )
        else:
            raise ATOperationError(f"不支持的导出规则: {export_rule}")
        
        print(f"导出成功: {output_path}")


classes = (
    FBXExportOperator,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 