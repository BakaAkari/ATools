from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty,
                       StringProperty)
from bpy.types import PropertyGroup
from bpy.utils import register_class, unregister_class
from ..config.constants import PhysicsSettings, ExportSettings, PathConstants


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
    
    export_rule: EnumProperty(
        items=[
            ('UNREAL', "Unreal", "Export as Unreal Engine rules"),
            ('UNITY', "Unity", "Export as Unity Engine rules"),
        ],
        name="Export Rule",
        description="Select an option",
        default='UNREAL'
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
    
    exportpath: StringProperty(
        name='Export Path',
        description='',
        default='',
        subtype=PathConstants.DEFAULT_EXPORT_SUBTYPE  # 指定为目录路径
    ) # type: ignore
    
    movetexlocation: BoolProperty(
        description="",
        default=True
    ) # type: ignore


# 保持向后兼容
AtPropgroup = ToolProperties

classes = (ToolProperties,)


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls) 