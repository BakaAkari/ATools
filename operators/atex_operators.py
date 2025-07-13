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


class ATexCreateMaterialOperator(bpy.types.Operator):
    """根据资产名和贴图自动创建UE材质"""
    bl_idname = "atex.create_material"
    bl_label = "创建材质"

    def execute(self, context):
        import_node_name = "UE Shader"
        wm = context.window_manager
        atex_props = wm.atex_props
        output_dir = bpy.path.abspath(atex_props.output_path)
        asset_name = atex_props.asset_name.strip()
        if not output_dir or not os.path.isdir(output_dir):
            self.report({'ERROR'}, "请先设置有效的输出路径")
            return {'CANCELLED'}
        if not asset_name:
            self.report({'ERROR'}, "请先输入资产名")
            return {'CANCELLED'}
        # 检查贴图文件是否存在
        found = False
        for suffix in ["Col", "ORM", "Nor", "Emi"]:
            fname = f"T_{asset_name}_{suffix}.png"
            if os.path.exists(os.path.join(output_dir, fname)):
                found = True
                break
        if not found:
            self.report({'ERROR'}, f"输出路径下未找到以T_{asset_name}_开头的贴图文件")
            return {'CANCELLED'}
        # 创建新材质
        mat_name = f"MI_{asset_name}"
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        links = node_tree.links
        # 查找并删除BSDF节点，记录其位置
        bsdf_node = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf_node = node
                break
        if bsdf_node:
            loc = bsdf_node.location.copy()
            nodes.remove(bsdf_node)
        else:
            loc = (0, 0)
        # 选中新建材质
        if context.active_object:
            context.active_object.active_material = mat
        # 查找材质输出节点
        output_node = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                output_node = node
                break
        if not output_node:
            output_node = nodes.new('ShaderNodeOutputMaterial')
            output_node.location = (loc[0]+400, loc[1])
        # 检查是否已有UE Shader节点组
        ue_group_node = None
        for node in nodes:
            if node.type == 'GROUP' and node.node_tree and node.node_tree.name == import_node_name:
                ue_group_node = node
                break
        if not ue_group_node:
            # 确保节点组已加载
            if not bpy.data.node_groups.get(import_node_name):
                bpy.ops.node.create_ue_pbr_group()
            # 新建节点组实例
            ue_group_node = nodes.new('ShaderNodeGroup')
            ue_group_node.node_tree = bpy.data.node_groups[import_node_name]
        # 放置UE Shader节点组在输出节点左侧200
        ue_group_node.location = (output_node.location[0] - 200, output_node.location[1])
        # 自动连接BSDF输出到Surface输入
        # 查找BSDF输出口
        bsdf_out = None
        for out in ue_group_node.outputs:
            if out.name.lower() == 'bsdf':
                bsdf_out = out
                break
        # 查找Surface输入口
        surface_in = None
        for inp in output_node.inputs:
            if inp.name.lower() == 'surface':
                surface_in = inp
                break
        # 连接
        if bsdf_out and surface_in:
            links.new(ue_group_node.outputs[bsdf_out.name], output_node.inputs[surface_in.name])
        # 自动创建贴图节点并连接
        tex_types = [
            ("Col", "DIF", "Alpha"),
            ("ORM", "ORM", None),
            ("Nor", "NRM", None),
            ("Emi", "Emission Color", "Emission Strength")
        ]
        tex_nodes = []
        tex_y_start = ue_group_node.location[1] + 220 * (len(tex_types)-1) // 2
        tex_x = ue_group_node.location[0] - 400
        found_tex = 0
        for idx, (suffix, ue_input, alpha_input) in enumerate(tex_types):
            tex_path = os.path.join(output_dir, f"T_{asset_name}_{suffix}.png")
            if not os.path.exists(tex_path):
                if suffix == "Emi":
                    continue  # Emi可选
                else:
                    continue  # 其他贴图理论上已检查过
            # 加载图片到Blender
            img = None
            for im in bpy.data.images:
                if os.path.abspath(bpy.path.abspath(im.filepath)) == os.path.abspath(tex_path):
                    img = im
                    break
            if not img:
                img = bpy.data.images.load(tex_path)
            # 创建Texture节点
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = img
            tex_node.label = suffix + " Tex Node"
            tex_node.location = (tex_x, tex_y_start - found_tex * 220)
            # 设置色彩空间
            if suffix in ("ORM", "Nor"):
                tex_node.image.colorspace_settings.name = 'Non-Color'
            tex_nodes.append((suffix, tex_node, ue_input, alpha_input))
            found_tex += 1
        # 自动连接贴图节点到UE Shader节点
        for suffix, tex_node, ue_input, alpha_input in tex_nodes:
            # 连接Color到主输入
            for inp in ue_group_node.inputs:
                if inp.name == ue_input:
                    links.new(tex_node.outputs['Color'], ue_group_node.inputs[ue_input])
            # 连接Alpha到副输入（如有）
            if alpha_input and 'Alpha' in tex_node.outputs:
                for inp in ue_group_node.inputs:
                    if inp.name == alpha_input:
                        links.new(tex_node.outputs['Alpha'], ue_group_node.inputs[alpha_input])
        self.report({'INFO'}, f"已创建材质: {mat_name} 并放置UE Shader节点组")
        return {'FINISHED'}


classes = (
    ATexPickNodeOperator,
    ATexMergeTexturesOperator,
    ATexCreateMaterialOperator,
)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 