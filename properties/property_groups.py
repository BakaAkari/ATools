import bpy
import mathutils
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty,
                       StringProperty, PointerProperty)
from bpy.types import PropertyGroup
from bpy.utils import register_class, unregister_class
from ..config.constants import PhysicsSettings, PathConstants

# 全局缓存存储初始位置，使用 window_manager id 作为 key
_initial_positions_cache = {}


def get_collection_items(self, context):
    """获取场景中所有集合的枚举项"""
    items = []
    for collection in bpy.data.collections:
        items.append((collection.name, collection.name, f"集合: {collection.name}"))
    return items


def get_initial_positions_from_cache(wm_id):
    """从缓存获取初始位置"""
    global _initial_positions_cache
    return _initial_positions_cache.get(wm_id, {})


def update_explode_offset(self, context):
    """当偏移值改变时实时更新对象位置"""
    global _initial_positions_cache
    
    # 从全局缓存获取初始位置
    wm_id = context.window_manager.as_pointer()
    initial_positions = _initial_positions_cache.get(wm_id, {})
    
    # 如果没有记录初始位置，直接返回
    if not self.has_initial_positions or not initial_positions:
        return
    
    # 如果没有选择集合，直接返回
    if not self.target_collection:
        return
    
    # 获取目标集合
    collection = bpy.data.collections.get(self.target_collection)
    if not collection:
        return
    
    # 获取集合中的所有网格对象
    mesh_objects = [obj for obj in collection.all_objects if obj.type == 'MESH']
    
    # 为每个对象计算偏移
    for obj in mesh_objects:
        # 使用对象指针作为key，避免重名问题
        obj_key = id(obj)
        if obj_key not in initial_positions:
            continue
        
        initial_world_center = initial_positions[obj_key]
        
        # 计算方向向量
        direction = initial_world_center.normalized() if initial_world_center.length > 0.001 else mathutils.Vector((1, 0, 0))
        
        # 计算偏移向量（基于初始位置 + 偏移值）
        offset_vector = direction * (initial_world_center.length + self.explode_offset)
        
        # 设置新位置
        obj.location = offset_vector


class ExplodeProperties(PropertyGroup):
    """拆件爆炸图属性组"""
    
    # 选择的集合
    target_collection: EnumProperty(
        name="目标集合",
        description="选择要进行爆炸图操作的集合",
        items=get_collection_items,
        default=0
    ) # type: ignore
    
    # 偏移值
    explode_offset: FloatProperty(
        name="偏移值",
        description="爆炸图偏移距离",
        default=0.0,
        min=-100.0,
        max=100.0,
        step=0.1,
        update=update_explode_offset
    ) # type: ignore
    
    # 是否已记录初始位置
    has_initial_positions: BoolProperty(
        name="Has Initial Positions",
        description="Whether initial positions have been recorded",
        default=False
    ) # type: ignore
    
    def record_initial_positions(self):
        """记录集合中所有对象的初始位置"""
        global _initial_positions_cache
        
        # 如果没有选择集合，直接返回
        if not self.target_collection:
            return {}
        
        # 获取目标集合
        collection = bpy.data.collections.get(self.target_collection)
        if not collection:
            return {}
        
        # 获取集合中的所有网格对象
        mesh_objects = [obj for obj in collection.all_objects if obj.type == 'MESH']
        
        if len(mesh_objects) == 0:
            return {}
        
        # 记录初始位置（使用对象指针作为key）
        initial_positions = {}
        
        for obj in mesh_objects:
            # 计算网格的重心（本地空间）
            mesh = obj.data
            if len(mesh.vertices) == 0:
                continue
            
            local_center = sum((mesh.vertices[i].co for i in range(len(mesh.vertices))), start=type(mesh.vertices[0].co)((0,0,0)))
            local_center /= len(mesh.vertices)
            
            # 转换为世界空间
            world_center = obj.matrix_world @ mathutils.Vector(local_center)
            
            # 使用对象指针作为key，避免重名问题
            obj_key = id(obj)
            initial_positions[obj_key] = world_center.copy()
        
        self.has_initial_positions = True
        return initial_positions
    



class AToolsToolProperties(PropertyGroup):
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
ToolProperties = AToolsToolProperties  # 别名
AtPropgroup = AToolsToolProperties

# 注册顺序很重要：先注册子类，再注册父类
classes = (ExplodeProperties, AToolsToolProperties)


def register():
    """注册属性组"""
    global classes
    for cls in classes:
        register_class(cls)
    
    # 注册后添加嵌套属性
    # 注意：这里添加的 PointerProperty 会在类上，而不是实例上
    # 这是 Blender 的推荐做法，用于在类定义后添加属性


def unregister():
    """注销属性组"""
    global classes
    # 注意：不需要删除 PointerProperty，它们会自动清理
    for cls in reversed(classes):  # 反向注销
        unregister_class(cls)
    
    # 清理全局缓存
    global _initial_positions_cache
    _initial_positions_cache.clear() 