import bpy
from bpy.utils import register_class, unregister_class
from ..utils.common_utils import ATOperationError


class CollectionSortOperator(bpy.types.Operator):
    """对选中集合中的子集合按英文字母A-Z排序"""
    bl_idname = "collection.sort_collections"
    bl_label = "Sort Collection"
    bl_description = "Sort child collections alphabetically (A-Z)"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 集合属性，用于传递目标集合
    collection_name: bpy.props.StringProperty(
        name="Collection Name",
        description="Name of the collection to sort",
        default=""
    )

    @classmethod
    def poll(cls, context):
        """检查是否可以执行此操作"""
        # 总是允许执行，在execute中处理错误情况
        return True

    def execute(self, context):
        try:
            # 获取目标集合
            target_collection = None
            
            # 方法1: 如果指定了集合名称，优先使用
            if self.collection_name:
                target_collection = bpy.data.collections.get(self.collection_name)
            
            # 方法2: 尝试从context获取
            if not target_collection:
                if hasattr(context, 'collection') and context.collection:
                    target_collection = context.collection
            
            # 方法3: 从outliner中的ID获取 (这是outliner操作的标准方法)
            if not target_collection:
                # 检查outliner中选择的项目
                if hasattr(context, 'id') and context.id and isinstance(context.id, bpy.types.Collection):
                    target_collection = context.id
            
            # 方法4: 使用活动对象所在的集合
            if not target_collection:
                if context.active_object and context.active_object.users_collection:
                    # 弹出对话框让用户选择要排序的集合
                    collections = context.active_object.users_collection
                    if len(collections) == 1:
                        target_collection = collections[0]
                    else:
                        # 如果对象在多个集合中，使用第一个
                        target_collection = collections[0]
            
            # 方法5: 最后使用场景主集合
            if not target_collection:
                target_collection = context.scene.collection
            
            if not target_collection:
                self.report({'ERROR'}, "无法确定要排序的集合")
                return {'CANCELLED'}
            
            # 执行排序
            if self._sort_child_collections(target_collection):
                self.report({'INFO'}, f"已对集合 '{target_collection.name}' 的子集合进行排序")
            else:
                self.report({'WARNING'}, f"集合 '{target_collection.name}' 没有需要排序的子集合")
                
            return {'FINISHED'}
            
        except ATOperationError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"排序集合失败: {str(e)}")
            return {'CANCELLED'}
    
    def _sort_child_collections(self, parent_collection):
        """对指定集合的子集合进行排序"""
        if not parent_collection:
            return False
            
        # 获取所有子集合
        child_collections = list(parent_collection.children)
        
        if len(child_collections) <= 1:
            return False  # 没有足够的子集合需要排序
            
        # 按名称排序（不区分大小写）
        child_collections.sort(key=lambda x: x.name.lower())
        
        # 重新排列子集合
        # 在Blender中，collection的children是一个特殊的集合，需要特殊处理
        try:
            # 记录原始的子集合
            original_children = list(parent_collection.children)
            
            # 检查是否需要重新排序
            sorted_names = [c.name for c in child_collections]
            original_names = [c.name for c in original_children]
            
            if sorted_names == original_names:
                return False  # 已经是正确的顺序
            
            # 清除所有子集合链接
            for child in original_children:
                parent_collection.children.unlink(child)
            
            # 按照排序后的顺序重新添加
            for child in child_collections:
                parent_collection.children.link(child)
                
            # 刷新视图
            bpy.context.view_layer.update()
                
            return True
            
        except Exception as e:
            # 如果出错，尝试恢复原始状态
            try:
                for child in child_collections:
                    if child.name not in [c.name for c in parent_collection.children]:
                        parent_collection.children.link(child)
            except:
                pass
            raise e


class CollectionContextMenu(bpy.types.Menu):
    """集合右键菜单"""
    bl_idname = "OUTLINER_MT_collection_context_menu_custom"
    bl_label = "Collection Context Menu"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        layout.operator("collection.sort_collections", text="Sort Collection", icon='SORTALPHA')


def collection_context_menu_draw(self, context):
    """在集合右键菜单中添加排序选项"""
    layout = self.layout
    layout.separator()
    
    # 尝试获取当前的集合
    current_collection = None
    if hasattr(context, 'collection') and context.collection:
        current_collection = context.collection
    elif hasattr(context, 'id') and context.id and isinstance(context.id, bpy.types.Collection):
        current_collection = context.id
    
    # 添加排序操作
    op = layout.operator("collection.sort_collections", text="Sort Collection", icon='SORTALPHA')
    if current_collection:
        op.collection_name = current_collection.name


# 操作符和菜单类列表
classes = (
    CollectionSortOperator,
    CollectionContextMenu,
)


def register():
    """注册所有类"""
    global classes
    for cls in classes:
        register_class(cls)
    
    # 添加到集合右键菜单
    bpy.types.OUTLINER_MT_collection.append(collection_context_menu_draw)


def unregister():
    """注销所有类"""
    global classes
    for cls in classes:
        unregister_class(cls)
    
    # 从集合右键菜单中移除
    bpy.types.OUTLINER_MT_collection.remove(collection_context_menu_draw) 