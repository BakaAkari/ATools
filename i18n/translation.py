# 翻译系统模块
import bpy
from typing import Dict, Optional

class TranslationManager:
    """翻译管理器"""
    
    def __init__(self):
        self._translations = self._load_translations()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """加载翻译数据"""
        return {
            # 按钮文本
            "Switch CH": {"en_US": "Switch CH", "zh": "切换中文"},
            "切换英文": {"en_US": "Switch EN", "zh": "切换英文"},
            "Reload Images": {"en_US": "Reload Images", "zh": "重新载入图像"},
            "Start": {"en_US": "Start", "zh": "开始"},
            "End": {"en_US": "End", "zh": "结束"},
            "Set Loop": {"en_US": "Set Loop", "zh": "设置循环"},
            
            # 操作符标签
            "开启自适应细分": {"en_US": "Enable Adaptive Subdivision", "zh": "开启自适应细分"},
            "Toggle map mapping": {"en_US": "Toggle Map Mapping", "zh": "切换映射方式"},
            "Reload Image": {"en_US": "Reload Image", "zh": "重新载入图像"},
            "ATTestOperator": {"en_US": "AT Test Operator", "zh": "AT测试操作"},

            "切换中英文": {"en_US": "Toggle Language", "zh": "切换中英文"},
            "导出FBX": {"en_US": "Export FBX", "zh": "导出FBX"},

            "Calculate Physics": {"en_US": "Calculate Physics", "zh": "计算物理"},
            "Add physics to Assets": {"en_US": "Add Physics to Assets", "zh": "为资产添加物理"},
            "Apply physics to Assets": {"en_US": "Apply Physics to Assets", "zh": "应用物理到资产"},
            "Quick Physics": {"en_US": "Quick Physics", "zh": "快速物理"},
            
            # UE PBR节点组相关
            "Create UE PBR Node Group": {"en_US": "Create UE PBR Node Group", "zh": "创建 UE PBR 节点组"},
            "Unreal Engine PBR": {"en_US": "Unreal Engine PBR", "zh": "虚幻引擎 PBR"},
            "Node Group Tools": {"en_US": "Node Group Tools", "zh": "节点组工具"},
            "UE PBR Material": {"en_US": "UE PBR Material", "zh": "UE PBR 材质"},
            "Already Exists": {"en_US": "Already Exists", "zh": "已存在"},
            "Drag from Add Menu": {"en_US": "Drag from Add Menu", "zh": "可从添加菜单拖拽"},
            
            # 面板标题
            "Game Engine Operator": {"en_US": "Game Engine Operator", "zh": "游戏引擎操作"},
            "Object Operator": {"en_US": "Object Operator", "zh": "对象操作"},
            "Image Operator": {"en_US": "Image Operator", "zh": "图像操作"},
            "AT Operator": {"en_US": "AT Operator", "zh": "AT 操作"},
            "Bridge Operator": {"en_US": "Bridge Operator", "zh": "Bridge 操作"},
            
            # 操作按钮
            "Export Object": {"en_US": "Export Object", "zh": "导出对象"},
            "Rename Object": {"en_US": "Rename Object", "zh": "重命名对象"},
            "Clean Object": {"en_US": "Clean Object", "zh": "清理对象"},
            "Resize Mesh": {"en_US": "Resize Mesh", "zh": "调整网格"},
            "切换映射方式": {"en_US": "Toggle Mapping", "zh": "切换映射方式"},
            "开启曲面细分": {"en_US": "Enable Subdivision", "zh": "开启曲面细分"},
            "开始模拟": {"en_US": "Start Simulation", "zh": "开始模拟"},
            "Cancel Calculation": {"en_US": "Cancel Calculation", "zh": "取消计算"},
            
            # 属性标签
            "Export Rule": {"en_US": "Export Rule", "zh": "导出规则"},
            "Export Location": {"en_US": "Export Location", "zh": "导出位置"},
            "Friction": {"en_US": "Friction", "zh": "摩擦力"},
            "Time Scale": {"en_US": "Time Scale", "zh": "时间缩放"},
            "Tiling Scale": {"en_US": "Tiling Scale", "zh": "平铺缩放"},
            "Bump Strength": {"en_US": "Bump Strength", "zh": "凹凸强度"},
            
            # 爆炸图相关
            "Explode View": {"en_US": "Explode View", "zh": "拆件爆炸图"},
            "Target Collection": {"en_US": "Target Collection", "zh": "目标集合"},
            "Record Initial Positions": {"en_US": "Record Initial Positions", "zh": "记录初始位置"},
            "Reset Positions": {"en_US": "Reset Positions", "zh": "重置位置"},
            "✓ Recorded Initial Positions": {"en_US": "✓ Recorded Initial Positions", "zh": "✓ 已记录初始位置"},
            "⚠ Please Record Initial Positions": {"en_US": "⚠ Please Record Initial Positions", "zh": "⚠ 请先记录初始位置"},
            "Offset Value": {"en_US": "Offset Value", "zh": "偏移值"},
            "Recorded {0} objects' initial positions": {"en_US": "Recorded {0} objects' initial positions", "zh": "已记录 {0} 个对象的初始位置"},
            "Failed to record initial positions: please select target collection first": {"en_US": "Failed to record initial positions: please select target collection first", "zh": "记录初始位置失败：请先选择目标集合"},
            "Reset all objects to initial positions": {"en_US": "Reset all objects to initial positions", "zh": "已重置所有对象到初始位置"},
            
            # 错误和警告信息（ATex翻译已移除，迁移到ATexLink插件）
        }
    
    def get_text(self, key: str, context: Optional[bpy.types.Context] = None) -> str:
        """获取翻译后的文本"""
        if context is None:
            context = bpy.context
        
        # 获取当前语言设置
        current_lang = context.preferences.view.language
        is_chinese = current_lang not in ["en_US"]
        
        # 从翻译字典获取文本
        if key in self._translations:
            lang_key = "zh" if is_chinese else "en_US"
            return self._translations[key].get(lang_key, key)
        
        # 如果没有找到翻译，返回原文本
        return key
    
    def add_translation(self, key: str, en_text: str, zh_text: str):
        """动态添加翻译"""
        self._translations[key] = {"en_US": en_text, "zh": zh_text}
    
    def is_chinese_language(self, context: Optional[bpy.types.Context] = None) -> bool:
        """检查当前是否为中文语言"""
        if context is None:
            context = bpy.context
        return context.preferences.view.language not in ["en_US"]


# 全局翻译管理器实例
_translation_manager = TranslationManager()

def get_text(key: str, context: Optional[bpy.types.Context] = None) -> str:
    """获取翻译文本的便捷函数"""
    return _translation_manager.get_text(key, context)

def add_translation(key: str, en_text: str, zh_text: str):
    """添加翻译的便捷函数"""
    _translation_manager.add_translation(key, en_text, zh_text)

def is_chinese_language(context: Optional[bpy.types.Context] = None) -> bool:
    """检查是否为中文语言的便捷函数"""
    return _translation_manager.is_chinese_language(context) 