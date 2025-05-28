import bpy
import numpy as np
import os
from .ATUtils import messagebox, open_system_directory, convert_blender_image_to_pil, check_pil_required

def translationui(self, context):
    layout = self.layout
    if context.preferences.view.language == "en_US":
        buttonname = "Switch CH"
    else:
        buttonname = "切换英文"
        
    layout.operator(operator="object.translation", text=buttonname)

def stop_playback(scene):
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=False)
    print("Stop Loop")

def start_playback(scene):
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=True)
    print("Start Loop")

def setframe(self, context):
    try:
        layout = self.layout
        layout.operator("object.setstartframe", text=r"Start", emboss=True, depress=False, icon_value=0)
        layout.operator("object.setendframe", text=r"End", emboss=True, depress=False, icon_value=0)
        layout.operator("object.stoploop", text=r"Set Loop", emboss=True, depress=False, icon_value=0)

    except Exception as exc:
        print(str(exc) + " | Error in Dopesheet Ht Header when adding to menu")

@check_pil_required
def SavePILImage(blend_file_directory, BID, TexNode, pil_image):
    NewTexPath = os.path.join(blend_file_directory, "Merge Tex", BID, TexNode.image.name)
    os.path.exists(os.path.dirname(NewTexPath)) or os.makedirs(os.path.dirname(NewTexPath))
    pil_image.save(NewTexPath) 
    pass

@check_pil_required
def BridgePILMergeCol(BID, ColNodeList):
    from PIL import Image

    for colnode in ColNodeList:
        if colnode.name == "Color Tex Node":
            ColTex = Image.open(colnode.image.filepath)
            TexName = colnode.image.name
        elif colnode.name == "Opacity Tex Node":
            OpacityTex = Image.open(colnode.image.filepath)
            
    if len(ColNodeList) > 1:
        NewColTex = Image.merge("RGBA", (ColTex.split()[0], ColTex.split()[1], ColTex.split()[2], OpacityTex.split()[0]))
    else:
        NewColTex = Image.merge("RGB", (ColTex.split()[0], ColTex.split()[1], ColTex.split()[2]))
    
    blend_file_path = bpy.data.filepath
    if blend_file_path:
        blend_file_directory = os.path.dirname(blend_file_path)
        NewColTexPath = os.path.join(blend_file_directory, "Merge Tex", BID, TexName)
        os.path.exists(os.path.dirname(NewColTexPath)) or os.makedirs(os.path.dirname(NewColTexPath))
        NewColTex.save(NewColTexPath)
    else:
        messagebox("Please save the file first", "Warning", "ERROR")

@check_pil_required
def BridgePILMergeORM(BID, ORMNodeList):
    from PIL import Image
    AOTex = None
    RoughnessTex = None
    MetalnessTex = None

    for ORMNode in ORMNodeList:
        if ORMNode.name == "AO Tex Node":
            AOTex = Image.open(ORMNode.image.filepath)
        if ORMNode.name == "Roughness Tex Node":
            RoughnessTex = Image.open(ORMNode.image.filepath)
            TexName = ORMNode.image.name.replace("Roughness", "ORM")
        if ORMNode.name == "Metalness Tex Node":
            MetalnessTex = Image.open(ORMNode.image.filepath)
            
    if RoughnessTex:
        if AOTex:
            if MetalnessTex:
                NewORMTex = Image.merge("RGB", (AOTex.split()[0], RoughnessTex.split()[0], MetalnessTex.split()[0]))
            else:
                NewORMTex = Image.merge("RGB", (AOTex.split()[0], RoughnessTex.split()[0], Image.new('L', RoughnessTex.size, 0)))
        else:
            NewORMTex = Image.merge("RGB", (Image.new('L', RoughnessTex.size, 256), RoughnessTex.split()[0], Image.new('L', RoughnessTex.size, 0)))
    else:
        pass
            
    blend_file_path = bpy.data.filepath
    if blend_file_path:
        blend_file_directory = os.path.dirname(blend_file_path)
        
        NewORMTexPath = os.path.join(blend_file_directory, "Merge Tex", BID, TexName)
        os.path.exists(os.path.dirname(NewORMTexPath)) or os.makedirs(os.path.dirname(NewORMTexPath))
        NewORMTex.save(NewORMTexPath)
        return NewORMTexPath
    else:
        messagebox("Please save the file first", "Warning", "ERROR")

@check_pil_required
def OrganizeImages(BID, NrmNodeList, DisNodeList):
    blend_file_path = bpy.data.filepath
    blend_file_directory = os.path.dirname(blend_file_path)
    
    if blend_file_path:
        for NrmNode in NrmNodeList:
            if NrmNode.name == "Normal Tex Node":
                NrmTex = convert_blender_image_to_pil(NrmNode)
                SavePILImage(blend_file_directory, BID, NrmNode, NrmTex)

@check_pil_required
def ManualPILMergeCol(ManualColNodeList):
    from PIL import Image
    wm = bpy.context.window_manager
    blend_file_path = bpy.data.filepath
    blend_file_directory = os.path.dirname(blend_file_path)

    if len(ManualColNodeList) > 1:
        for colnode in ManualColNodeList:
            if colnode.image.name == wm.atprops.col_tex_name:
                if os.path.isabs(colnode.image.filepath):
                    ColTex = Image.open(blend_file_directory + os.path.abspath(colnode.image.filepath))
                else:
                    ColTex = Image.open(os.path.abspath(colnode.image.filepath))
            elif colnode.name == wm.atprops.opa_tex_name:
                if os.path.isabs(colnode.image.filepath):
                    OpaTex = Image.open(blend_file_directory + os.path.abspath(colnode.image.filepath))
                    print(colnode)
                else:
                    OpaTex = Image.open(os.path.abspath(colnode.image.filepath))
                    print(colnode)
        return

@check_pil_required
def ManualPILMergeORM(actmat, ManualORMNodeList):
    from PIL import Image
    AOTex = None
    RoughnessTex = None
    MetalnessTex = None
    TexName = None  # Initialize TexName with None

    # Check if we have any nodes to process
    if not ManualORMNodeList:
        messagebox("No texture nodes provided for ORM merge", "Warning", "ERROR")
        return None

    for ORMNode in ManualORMNodeList:
        image_name = ORMNode.image.name.lower()  # Convert to lowercase for case-insensitive matching
        if 'ao' in image_name:
            AOTex = Image.open(ORMNode.image.filepath)
        if 'roughness' in image_name:
            RoughnessTex = Image.open(ORMNode.image.filepath)
            TempTexName = ORMNode.image.name.replace("Roughness", "ORM")
            TexName = actmat.name + '_' + TempTexName.split('_')[-1] + '.png'
        if 'metalness' in image_name:
            MetalnessTex = Image.open(ORMNode.image.filepath)
            
    # Check if we have at least Roughness texture
    if not RoughnessTex:
        messagebox("No Roughness texture found for ORM merge", "Warning", "ERROR")
        return None

    # Ensure TexName is set
    if not TexName:
        TexName = actmat.name + '_ORM.png'  # Default name if not set by Roughness texture
            
    if RoughnessTex:
        if AOTex:
            if MetalnessTex:
                NewORMTex = Image.merge("RGB", (AOTex.split()[0], RoughnessTex.split()[0], MetalnessTex.split()[0]))
            else:
                NewORMTex = Image.merge("RGB", (AOTex.split()[0], RoughnessTex.split()[0], Image.new('L', RoughnessTex.size, 0)))
        else:
            NewORMTex = Image.merge("RGB", (Image.new('L', RoughnessTex.size, 256), RoughnessTex.split()[0], Image.new('L', RoughnessTex.size, 0)))
    else:
        messagebox("Failed to create ORM texture", "Warning", "ERROR")
        return None
            
    blend_file_path = bpy.data.filepath
    if blend_file_path:
        blend_file_directory = os.path.dirname(blend_file_path)
        
        NewORMTexPath = os.path.join(blend_file_directory, "Merge Tex", actmat.name, TexName)
        os.path.exists(os.path.dirname(NewORMTexPath)) or os.makedirs(os.path.dirname(NewORMTexPath))
        NewORMTex.save(NewORMTexPath)
        return NewORMTexPath
    else:
        messagebox("Please save the file first", "Warning", "ERROR")
        return None

@check_pil_required
def ManualOrganizeImages(Mat, ManualColNodeList, ManualNrmNodeList):
    blend_file_path = bpy.data.filepath
    blend_file_directory = os.path.dirname(blend_file_path)
    
    if blend_file_path:
        for Colnode in ManualColNodeList:
            ColTex = convert_blender_image_to_pil(Colnode)
            # Get the base name without .00x suffix
            base_name = Colnode.image.name.rsplit("_", 1)[-1]
            if base_name.endswith(('.001', '.002', '.003', '.004', '.005')):
                base_name = base_name[:-4]  # Remove the .00x suffix
            NewTexName = Mat.name + '_' + base_name
            NewColTexPath = os.path.join(blend_file_directory, "Merge Tex", Mat.name, NewTexName)
            os.path.exists(os.path.dirname(NewColTexPath)) or os.makedirs(os.path.dirname(NewColTexPath))
            ColTex.save(NewColTexPath) 
                
        for NrmNode in ManualNrmNodeList:
            NrmTex = convert_blender_image_to_pil(NrmNode)
            # Get the base name without .00x suffix
            base_name = NrmNode.image.name.rsplit("_", 1)[-1]
            if base_name.endswith(('.001', '.002', '.003', '.004', '.005')):
                base_name = base_name[:-4]  # Remove the .00x suffix
            NewTexName = Mat.name + '_' + base_name
            NewNrmTexPath = os.path.join(blend_file_directory, "Merge Tex", Mat.name, NewTexName)
            os.path.exists(os.path.dirname(NewNrmTexPath)) or os.makedirs(os.path.dirname(NewNrmTexPath))
            NrmTex.save(NewNrmTexPath) 
        
        return NewColTexPath, NewNrmTexPath
