import os
import bpy
import subprocess
import json
from bpy.utils import register_class, unregister_class
from ..utils.common_utils import ATOperationError


class ATexPickNodeOperator(bpy.types.Operator):
    """拾取节点操作符"""
    bl_idname = "atex.pick_node"
    bl_label = "拾取节点"
    
    node_property: bpy.props.StringProperty()
    
    def execute(self, context):
        try:
            # 获取当前选中的节点
            active_node = context.active_node
            
            if not active_node:
                self.report({'ERROR'}, "请先选择一个节点")
                return {'CANCELLED'}
            
            # 检查节点类型是否为TEXTURE类型
            if active_node.type != 'TEX_IMAGE':
                self.report({'ERROR'}, "请选择一个TEXTURE类型的节点")
                return {'CANCELLED'}
            
            # 检查节点是否有图像
            if not active_node.image:
                self.report({'ERROR'}, "选择的节点没有图像")
                return {'CANCELLED'}
            
            # 更新对应的属性
            wm = context.window_manager
            atex_props = wm.atex_props
            setattr(atex_props, self.node_property, active_node.name)
            
            # 显示贴图名称
            texture_name = active_node.image.name
            self.report({'INFO'}, f"已拾取节点: {active_node.name}, 贴图: {texture_name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"拾取节点失败: {str(e)}")
            return {'CANCELLED'}


class ATexMergeTexturesOperator(bpy.types.Operator):
    """合并贴图操作符"""
    bl_idname = "atex.merge_textures"
    bl_label = "导出合并贴图"

    def execute(self, context):
        try:
            wm = context.window_manager
            atex_props = wm.atex_props
            
            # 检查是否启用ATex功能
            if not atex_props.enable_atex:
                self.report({'ERROR'}, "请在偏好设置中启用ATex功能")
                return {'CANCELLED'}
            
            # 检查ATex.exe路径
            if not atex_props.atex_exe_path:
                self.report({'ERROR'}, "请在偏好设置中设置ATex.exe路径")
                return {'CANCELLED'}
            
            # 验证ATex.exe文件是否存在
            atex_exe_path = bpy.path.abspath(atex_props.atex_exe_path)
            if not os.path.exists(atex_exe_path):
                self.report({'ERROR'}, f"ATex.exe文件不存在: {atex_exe_path}")
                return {'CANCELLED'}
            
            # 检查输出路径
            if not atex_props.output_path:
                self.report({'ERROR'}, "请先设置输出路径")
                return {'CANCELLED'}
            
            # 检查Col贴图是否已选择
            if not atex_props.col_node:
                self.report({'ERROR'}, "请先选择Col贴图节点")
                return {'CANCELLED'}
            
            # 验证Col节点是否存在且有图像
            if context.active_object and context.active_object.active_material:
                node_tree = context.active_object.active_material.node_tree
                if node_tree and atex_props.col_node in node_tree.nodes:
                    col_node = node_tree.nodes[atex_props.col_node]
                    if col_node.type != 'TEX_IMAGE' or not col_node.image:
                        self.report({'ERROR'}, "Col节点没有有效的图像")
                        return {'CANCELLED'}
                else:
                    self.report({'ERROR'}, "Col节点不存在")
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, "没有活动的材质")
                return {'CANCELLED'}
            
            # 收集所有已选择的节点并验证
            node_mapping = {
                'col_node': ('diffuse', 'Col'),
                'roug_node': ('roughness', 'Roug'),
                'meta_node': ('metallic', 'Meta'),
                'nor_node': ('normal', 'Nor'),
                'ao_node': ('ao', 'AO'),
                'opa_node': ('opacity', 'Opa'),
                'emic_node': ('emission_color', 'EmiC'),
                'emia_node': ('emission_alpha', 'EmiA')
            }
            
            # 验证所有节点并收集图像路径
            texture_paths = {}
            basename = None
            
            for prop_name, (atex_type, label) in node_mapping.items():
                node_name = getattr(atex_props, prop_name)
                if node_name:
                    # 检查节点是否存在于当前材质中
                    if context.active_object and context.active_object.active_material:
                        node_tree = context.active_object.active_material.node_tree
                        if node_tree and node_name in node_tree.nodes:
                            node = node_tree.nodes[node_name]
                            if node.type == 'TEX_IMAGE' and node.image:
                                # 获取图像文件路径
                                image_path = bpy.path.abspath(node.image.filepath_from_user())
                                if os.path.exists(image_path):
                                    texture_paths[atex_type] = image_path
                                    # 使用Col贴图的文件名作为basename
                                    if atex_type == 'diffuse' and basename is None:
                                        basename = os.path.splitext(os.path.basename(image_path))[0]
                                else:
                                    self.report({'WARNING'}, f"{label} 贴图文件不存在: {image_path}")
                            else:
                                self.report({'WARNING'}, f"{label} 节点没有图像或不是图像节点")
                        else:
                            self.report({'WARNING'}, f"{label} 节点不存在: {node_name}")
            
            # 检查必需的贴图
            required_textures = ['diffuse', 'ao', 'normal']
            missing_textures = [texture for texture in required_textures if texture not in texture_paths]
            if missing_textures:
                self.report({'ERROR'}, f"缺少必需的贴图: {', '.join(missing_textures)}")
                return {'CANCELLED'}
            
            if not basename:
                self.report({'ERROR'}, "无法获取基础文件名")
                return {'CANCELLED'}
            
            # 准备ATex.exe的CLI参数
            cmd_args = [atex_exe_path, 'orm']
            
            # 添加必需的参数
            cmd_args.extend(['--diffuse', texture_paths['diffuse']])
            cmd_args.extend(['--ao', texture_paths['ao']])
            cmd_args.extend(['--normal', texture_paths['normal']])
            
            # 添加可选的参数
            optional_mapping = {
                'roughness': '--roughness',
                'metallic': '--metallic',
                'opacity': '--opacity',
                'emission_color': '--emission-color',
                'emission_alpha': '--emission-alpha'
            }
            
            for texture_type, arg_name in optional_mapping.items():
                if texture_type in texture_paths:
                    cmd_args.extend([arg_name, texture_paths[texture_type]])
            
            # 资产名
            asset_name = atex_props.asset_name.strip()
            if not asset_name:
                self.report({'ERROR'}, "请先输入资产名")
                return {'CANCELLED'}
            
            # 添加输出参数
            output_dir = bpy.path.abspath(atex_props.output_path)
            cmd_args.extend(['--output-dir', output_dir])
            cmd_args.extend(['--basename', asset_name])
            
            # 执行ATex.exe
            self.report({'INFO'}, f"正在执行ATex合并操作...")
            self.report({'INFO'}, f"命令: {' '.join(cmd_args)}")
            
            try:
                result = subprocess.run(cmd_args, capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode == 0:
                    # 尝试解析JSON输出
                    try:
                        output_data = json.loads(result.stdout)
                        if output_data.get('status') == 'success':
                            self.report({'INFO'}, f"贴图合并成功: {output_data.get('message', '')}")
                        else:
                            self.report({'ERROR'}, f"ATex处理失败: {output_data.get('message', '')}")
                            return {'CANCELLED'}
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，直接显示输出
                        if result.stdout.strip():
                            self.report({'INFO'}, f"ATex输出: {result.stdout.strip()}")
                        else:
                            self.report({'INFO'}, "贴图合并成功")
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip() or "未知错误"
                    self.report({'ERROR'}, f"ATex执行失败: {error_msg}")
                    return {'CANCELLED'}
                
                # 打开输出目录
                try:
                    if os.path.exists(output_dir):
                        if os.name == 'nt':  # Windows
                            os.startfile(output_dir)
                        elif os.name == 'posix':  # macOS/Linux
                            subprocess.run(['open', output_dir] if os.uname().sysname == 'Darwin' else ['xdg-open', output_dir])
                        self.report({'INFO'}, f"已打开输出目录: {output_dir}")
                    else:
                        self.report({'WARNING'}, f"输出目录不存在: {output_dir}")
                except Exception as e:
                    self.report({'WARNING'}, f"无法打开输出目录: {str(e)}")
                
                return {'FINISHED'}
                
            except subprocess.SubprocessError as e:
                self.report({'ERROR'}, f"执行ATex.exe时出错: {str(e)}")
                return {'CANCELLED'}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"合并贴图失败: {str(e)}")
            return {'CANCELLED'}


classes = (
    ATexPickNodeOperator,
    ATexMergeTexturesOperator,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 