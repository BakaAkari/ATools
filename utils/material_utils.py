import bpy
from ..config.constants import MaterialNodes
from .common_utils import ATOperationError


def get_material_node_by_type(material, node_type):
    """根据类型获取材质节点"""
    if not material or not material.node_tree:
        return None
    
    for node in material.node_tree.nodes:
        if node.type == node_type:
            return node
    return None


def get_material_node_by_name(material, node_name):
    """根据名称获取材质节点"""
    if not material or not material.node_tree:
        return None
    
    try:
        return material.node_tree.nodes[node_name]
    except KeyError:
        return None


def has_material_node_type(material, node_type):
    """检查材质是否有指定类型的节点"""
    return get_material_node_by_type(material, node_type) is not None


def get_texture_image_from_material(material):
    """从材质获取纹理图像"""
    if not material or not material.node_tree:
        return None
    
    for node in material.node_tree.nodes:
        if node.type == MaterialNodes.TEX_IMAGE and node.image:
            return node.image
    return None


def setup_material_projection(material, projection_type):
    """设置材质投影类型"""
    if not material or not material.node_tree:
        raise ATOperationError("无效的材质")
    
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # 查找必要的节点
    texcoord_node = get_material_node_by_type(material, MaterialNodes.TEX_COORD)
    mapping_node = get_material_node_by_type(material, MaterialNodes.MAPPING)
    
    if not texcoord_node or not mapping_node:
        raise ATOperationError("材质缺少必要的纹理坐标或映射节点")
    
    # 设置所有纹理节点的投影类型
    for node in nodes:
        if node.type == MaterialNodes.TEX_IMAGE:
            node.projection = projection_type
            if projection_type == MaterialNodes.PROJECTION_BOX:
                node.projection_blend = MaterialNodes.DEFAULT_PROJECTION_BLEND
                # 连接Object输出到映射节点
                links.new(texcoord_node.outputs["Object"], mapping_node.inputs["Vector"])
            elif projection_type == MaterialNodes.PROJECTION_FLAT:
                # 连接UV输出到映射节点
                links.new(texcoord_node.outputs["UV"], mapping_node.inputs["Vector"])


def get_bridge_material_properties(material):
    """获取Bridge材质的属性"""
    if not material or not material.node_tree:
        return None
    
    nodes = material.node_tree.nodes
    properties = {}
    
    # 获取Tiling Scale
    tiling_node = get_material_node_by_name(material, MaterialNodes.TILING_SCALE)
    if tiling_node:
        properties['tiling_scale'] = tiling_node.outputs['Value'].default_value
    
    # 获取Bump Strength
    bump_node = get_material_node_by_name(material, MaterialNodes.BUMP_STRENGTH)
    if bump_node:
        properties['bump_strength'] = bump_node.outputs['Value'].default_value
    
    return properties if properties else None


def set_bridge_material_properties(material, properties):
    """设置Bridge材质的属性"""
    if not material or not material.node_tree:
        raise ATOperationError("无效的材质")
    
    nodes = material.node_tree.nodes
    
    # 设置Tiling Scale
    if 'tiling_scale' in properties:
        tiling_node = get_material_node_by_name(material, MaterialNodes.TILING_SCALE)
        if tiling_node:
            tiling_node.outputs['Value'].default_value = properties['tiling_scale']
    
    # 设置Bump Strength
    if 'bump_strength' in properties:
        bump_node = get_material_node_by_name(material, MaterialNodes.BUMP_STRENGTH)
        if bump_node:
            bump_node.outputs['Value'].default_value = properties['bump_strength'] 