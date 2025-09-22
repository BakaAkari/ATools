from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty,
                       StringProperty)
from bpy.types import PropertyGroup
from bpy.utils import register_class, unregister_class
from ..config.constants import PhysicsSettings, PathConstants


def update_atex_status(self, context):
    """当资产名或输出路径改变时更新状态"""
    # 触发UI更新
    try:
        bpy.ops.atex.check_file_conflicts()
    except:
        pass  # 如果操作符未注册，忽略错误


class ATexProperties(PropertyGroup):
    """ATex工具属性组"""
    
    # 启用ATex功能
    enable_atex: BoolProperty(
        name="启用ATex图像处理功能",
        description="启用ATex图像处理功能",
        default=True
    ) # type: ignore
    
    # ATex.exe路径
    atex_exe_path: StringProperty(
        name="ATex.exe路径",
        description="选择ATex.exe文件路径",
        default="D:/NextCloud/Code/Python/Baka Akari Tools Bag/ATex/dist/ATexTool.exe",
        subtype='FILE_PATH'
    ) # type: ignore
    
    # 8个节点引用属性
    col_node: StringProperty(
        name="Col",
        description="选择颜色贴图节点",
        default=""
    ) # type: ignore
    
    roug_node: StringProperty(
        name="Roug", 
        description="选择粗糙度贴图节点",
        default=""
    ) # type: ignore
    
    meta_node: StringProperty(
        name="Meta",
        description="选择金属度贴图节点", 
        default=""
    ) # type: ignore
    
    nor_node: StringProperty(
        name="Nor",
        description="选择法线贴图节点",
        default=""
    ) # type: ignore
    
    ao_node: StringProperty(
        name="AO",
        description="选择环境光遮蔽贴图节点",
        default=""
    ) # type: ignore
    
    opa_node: StringProperty(
        name="Opa",
        description="选择不透明度贴图节点",
        default=""
    ) # type: ignore
    
    disp_node: StringProperty(
        name="Disp",
        description="选择位移贴图节点",
        default=""
    ) # type: ignore
    
    emia_node: StringProperty(
        name="EmiA",
        description="选择发光强度贴图节点",
        default=""
    ) # type: ignore
    
    # 资产名
    asset_name: StringProperty(
        name="资产名",
        description="输出文件的资产名（如：MyRock）",
        default="",
        update=update_atex_status
    ) # type: ignore

    # 输出路径
    output_path: StringProperty(
        name="输出路径",
        description="选择合并贴图的输出路径",
        default="",
        subtype='DIR_PATH',
        update=update_atex_status
    ) # type: ignore
    
    # 命名规则
    naming_rule: StringProperty(
        name="命名规则",
        description="输出文件的命名规则，使用{basename}和{type}作为占位符",
        default="T_{basename}_{type}.png"
    ) # type: ignore
    
    # 翻转法线选项
    flip_normal: BoolProperty(
        name="翻转法线",
        description="在导出合并贴图时翻转Normal贴图",
        default=False
    ) # type: ignore
    
    # 图像缩放选项
    enable_resize: BoolProperty(
        name="启用缩放",
        description="在导出合并贴图时缩放所有贴图",
        default=False
    ) # type: ignore
    
    resize_width: IntProperty(
        name="宽度",
        description="目标宽度（像素）",
        default=512,
        min=1,
        max=10000
    ) # type: ignore
    
    resize_height: IntProperty(
        name="高度",
        description="目标高度（像素）",
        default=512,
        min=1,
        max=10000
    ) # type: ignore
    
    keep_aspect_ratio: BoolProperty(
        name="保持宽高比",
        description="缩放时保持原始宽高比",
        default=True
    ) # type: ignore
    
    resize_output_path: StringProperty(
        name="缩放输出路径",
        description="选择缩放后贴图的输出路径",
        default="",
        subtype='DIR_PATH'
    ) # type: ignore


class ToolProperties(PropertyGroup):
    """工具属性组"""
    
    my_bool: BoolProperty(
        name="Enable or Disable",
        description="A bool property",
        default=False
    ) # type: ignore

    my_int: IntProperty(
        name="Int Value",
        description="A integer property",
        default=23,
        min=10,
        max=100
    ) # type: ignore

    my_float: FloatProperty(
        name="Float Value",
        description="A float property",
        default=23.7,
        min=0.01,
        max=30.0
    ) # type: ignore

    my_float_vector: FloatVectorProperty(
        name="Float Vector Value",
        description="Something",
        default=(0.0, 0.0, 0.0),
        min=0.0,  # float
        max=0.1
    ) # type: ignore

    my_string: StringProperty(
        name="User Input",
        description=":",
        default="",
        maxlen=PathConstants.MAX_STRING_LENGTH,
    ) # type: ignore

    my_enum: EnumProperty(
        name="Dropdown:",
        description="Apply Data to attribute.",
        items=[('OP1', "Option 1", ""),
               ('OP2', "Option 2", ""),
               ('OP3', "Option 3", ""),
               ]
    ) # type: ignore
    
    
    physics_friction: FloatProperty(
        description="Friction",
        default=PhysicsSettings.DEFAULT_FRICTION,
        min=0.0, max=1.0
    ) # type: ignore
    
    physics_time_scale: FloatProperty(
        description="Simulation speed",
        default=PhysicsSettings.DEFAULT_TIME_SCALE, 
        min=0.0, max=20.0
    ) # type: ignore
    
    is_running_physics: BoolProperty(
        description="",
        default=False
    ) # type: ignore
    
    running_physics_calculation: BoolProperty(
        description="",
        default=False
    ) # type: ignore
    
    
    movetexlocation: BoolProperty(
        description="",
        default=True
    ) # type: ignore


# 保持向后兼容
AtPropgroup = ToolProperties

classes = (ToolProperties, ATexProperties,)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 