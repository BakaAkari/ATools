# ATools 常量定义文件

# 插件信息
PLUGIN_NAME = "ATools"
PLUGIN_VERSION = (0, 1, 5)
BLENDER_VERSION = (2, 8, 0)


# 物理设置常量
class PhysicsSettings:
    DEFAULT_FRICTION = 0.5
    DEFAULT_TIME_SCALE = 5.0
    MAX_SIMULATION_FRAMES = 10000
    DEFAULT_FPS = 24
    COLLISION_MARGIN = 0.0001


# UI 常量
class UIConstants:
    PANEL_CATEGORY = "ATB"
    PANEL_ORDER_MAIN = 1
    PANEL_ORDER_PHYSICS = 2
    PANEL_ORDER_NODE = 3

# 文件路径常量
class PathConstants:
    DEFAULT_EXPORT_SUBTYPE = 'DIR_PATH'
    MAX_STRING_LENGTH = 1024

# 材质节点常量
class MaterialNodes:
    TILING_SCALE = 'Tiling Scale'
    BUMP_STRENGTH = 'Bump Strength'
    BRIDGE_DISPLACEMENT = "Bridge Dispalcement"
    
    # 节点类型
    TEX_COORD = "TEX_COORD"
    MAPPING = "MAPPING"
    TEX_IMAGE = "TEX_IMAGE"
    SUBSURF = "SUBSURF"
    
    # 投影类型
    PROJECTION_BOX = "BOX"
    PROJECTION_FLAT = "FLAT"
    DEFAULT_PROJECTION_BLEND = 0.25



# 系统偏好设置常量
class PreferenceSettings:
    VIEWPORT_AA = "32"
    ANISOTROPIC_FILTER = "FILTER_16"
    UNDO_STEPS = 256
    DEFAULT_LANGUAGE_ZH = "zh_HANS"
    DEFAULT_LANGUAGE_EN = "en_US" 