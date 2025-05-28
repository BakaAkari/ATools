import bpy
from bpy.app.handlers import persistent
from bpy.props import PointerProperty

from . import ATOperator3D, ATPreferences, ATProps, ATFunctions, ATPanel, ATOperatorNode, QuickPhysics
from .ATProps import AtPropgroup
from .ATUtils import is_pil_available

bl_info = {
    "name": "ATools",
    "description": "Baka_Akari's fixed Quixel Bridge Link plugin suite",
    "author": "Baka_Akari",
    "version": (0, 0, 5),
    "blender": (2, 8, 0),
    "location": "View3D",
    "warning": "Multiple functions are in beta. Some features require PIL library.",  # used for warning icon and text in addons panel
    "wiki_url": "https://docs.quixel.org/bridge/livelinks/blender/info_quickstart.html",
    "support": "COMMUNITY",
    "category": "3D View"
}

def register():
    # 检查PIL是否可用
    if not is_pil_available():
        print("PIL library is not installed. Some features will be disabled.")
    
    ATPreferences.register()
    ATOperator3D.register()
    ATOperatorNode.register()
    ATProps.register()
    ATPanel.register()
    QuickPhysics.register()

    bpy.types.WindowManager.atprops = PointerProperty(type=AtPropgroup)
    bpy.types.WindowManager.quick_physics = PointerProperty(type=AtPropgroup)
    bpy.types.STATUSBAR_HT_header.append(ATFunctions.translationui)
    bpy.types.DOPESHEET_HT_header.append(ATFunctions.setframe)

def unregister():
    ATPreferences.unregister()
    ATOperator3D.unregister()
    ATOperatorNode.unregister()
    ATProps.unregister()
    ATPanel.unregister()
    QuickPhysics.unregister()
    
    del bpy.types.WindowManager.atprops
    del bpy.types.WindowManager.quick_physics
    bpy.types.STATUSBAR_HT_header.remove(ATFunctions.translationui)
    bpy.types.DOPESHEET_HT_header.remove(ATFunctions.setframe)

