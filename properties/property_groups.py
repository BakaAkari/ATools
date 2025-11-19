import bpy
import mathutils
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty,
                       StringProperty, PointerProperty)
from bpy.types import PropertyGroup
from bpy.utils import register_class, unregister_class
from ..config.constants import PhysicsSettings, PathConstants

# 全局缓存存储初始位置，使用 window_manager id 作为 key
# 存储格式: {obj_key: {'location': Vector, 'center': Vector, 'distance': float}, 'min_distance': float, 'max_distance': float}
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
    
    # 获取距离范围用于归一化
    min_distance = initial_positions.get('_min_distance', 0.0)
    max_distance = initial_positions.get('_max_distance', 1.0)
    distance_range = max_distance - min_distance if max_distance > min_distance else 1.0
    
    # 为每个对象计算偏移
    for obj in mesh_objects:
        # 使用对象指针作为key，避免重名问题
        obj_key = id(obj)
        if obj_key not in initial_positions:
            continue
        
        # 跳过距离范围标记
        if obj_key in ['_min_distance', '_max_distance']:
            continue
        
        # 获取记录的初始位置和重心
        initial_data = initial_positions[obj_key]
        initial_location = initial_data['location']
        initial_world_center = initial_data['center']
        distance = initial_data.get('distance', initial_world_center.length)
        
        # 根据距离计算缩放因子（距离越远，缩放因子越大）
        # 使用非线性映射以增强距离差异，更好地拉开密集区域
        if distance_range > 0.001:
            # 归一化距离到 0-1 范围
            normalized_distance = (distance - min_distance) / distance_range
            # 使用平方函数增强距离差异：距离越远，缩放因子增长越快
            # 映射到更大范围：[0.1, 3.0]，让距离远的对象偏移更多，拉开密集区域
            min_scale = 0.1
            max_scale = 3.0
            # 使用 normalized_distance 的平方，让距离差异更明显
            scale_factor = min_scale + (normalized_distance ** 2) * (max_scale - min_scale)
            scale_factor = max(0.1, scale_factor)  # 确保最小缩放因子
        else:
            # 如果所有对象距离相同，使用固定缩放
            scale_factor = 1.0
        
        # 计算归一化的方向向量（从原点到重心的方向）
        if initial_world_center.length > 0.001:
            direction = initial_world_center.normalized()
        else:
            # 如果重心在原点，使用默认方向
            direction = mathutils.Vector((1, 0, 0))
        
        # 计算偏移向量：使用归一化方向向量，距离越远偏移越多
        offset_vector = direction * self.explode_offset * scale_factor
        
        # 计算新位置：原始位置 + 偏移向量
        new_location = initial_location + offset_vector
        
        # 设置新位置
        obj.location = new_location


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
        distances = []
        
        for obj in mesh_objects:
            # 计算网格的重心（本地空间）
            mesh = obj.data
            if len(mesh.vertices) == 0:
                continue
            
            local_center = sum((mesh.vertices[i].co for i in range(len(mesh.vertices))), start=type(mesh.vertices[0].co)((0,0,0)))
            local_center /= len(mesh.vertices)
            
            # 转换为世界空间
            world_center = obj.matrix_world @ mathutils.Vector(local_center)
            
            # 计算到原点的距离
            distance = world_center.length
            
            # 使用对象指针作为key，避免重名问题
            obj_key = id(obj)
            # 同时记录对象的原始位置、重心坐标和距离
            initial_positions[obj_key] = {
                'location': mathutils.Vector(obj.location),
                'center': world_center.copy(),
                'distance': distance
            }
            distances.append(distance)
        
        # 记录距离范围用于归一化
        if distances:
            initial_positions['_min_distance'] = min(distances)
            initial_positions['_max_distance'] = max(distances)
        
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
    
    physics_solver_iterations: IntProperty(
        description="Solver precision",
        default=PhysicsSettings.DEFAULT_SOLVER_ITERATIONS,
        min=1, max=200
    ) # type: ignore
    
    physics_split_impulse: BoolProperty(
        description="Reduce penetration artifacts",
        default=PhysicsSettings.DEFAULT_SPLIT_IMPULSE
    ) # type: ignore
    
    physics_restitution: FloatProperty(
        description="Elasticity",
        default=PhysicsSettings.DEFAULT_RESTITUTION,
        min=0.0, max=1.0
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