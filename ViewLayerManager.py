import bpy
from bpy.types import Panel, UIList

#class VIEWLAYER_PT_layers(ViewLayerButtonsPanel, Panel):
#    bl_label = "Layer List"
#    bl_options = {'HIDE_HEADER'}
#    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}

#    def draw(self, context):
#        layout = self.layout

#        scene = context.scene
#        rd = scene.render

#        if rd.engine == 'BLENDER_GAME':
#            layout.label("Not available in the Game Engine")
#            return

#        row = layout.row()
#        col = row.column()
#        col.template_list("VIEWLAYER_UL_viewlayers", "", rd, "layers", rd.layers, "active_index", rows=2)

#        col = row.column()
#        sub = col.column(align=True)
#        sub.operator("scene.view_layer_add", icon='ZOOMIN', text="")
#        sub.operator("scene.view_layer_remove", icon='ZOOMOUT', text="")
#        col.prop(rd, "render_single_layer", icon_only=True)
        
def freestyleToDict(viewLayer):
    
    freestyleDict = {}
            
    freestyleProperties = [property for property in bpy.types.FreestyleSettings.bl_rna.properties]
                
    for freestyleProp in freestyleProperties:
        
        if freestyleProp.identifier == 'linesets':
            
            linesets = []
            
            for lineset in viewLayer.freestyle_settings.linesets:
                
                linesetDict = {}
                
                linesetProperties = [property for property in bpy.types.FreestyleLineSet.bl_rna.properties if not property.is_readonly]
                                
                for linesetProp in linesetProperties:
                    
                    linesetDict[linesetProp.identifier] = getattr(lineset, linesetProp.identifier)
                
                linesets.append(linesetDict)
                
            freestyleDict[freestyleProp.identifier] = linesets
            
            for lineset in viewLayer.freestyle_settings.linesets:
                
                viewLayer.freestyle_settings.linesets.remove(lineset)   
        
        if not freestyleProp.is_readonly:
        
            freestyleDict[freestyleProp.identifier] = getattr(viewLayer.freestyle_settings, freestyleProp.identifier)

    return freestyleDict



def viewLayerToDict(viewLayer):

    properties = [property for property in bpy.types.ViewLayer.bl_rna.properties]

    viewLayerDict = {}

    for prop in properties:
        
        #The '[:]' makes sure the data of a collection of values is copied instead of a reference to it        
        if prop.identifier in ['layers', 'layers_exclude', 'layers_zmask']:
            
            viewLayerDict[prop.identifier] = getattr(viewLayer, prop.identifier)[:]
        
        elif prop.identifier == 'freestyle_settings':
                            
            viewLayerDict[prop.identifier] = freestyleToDict(viewLayer)
        
        elif not prop.is_readonly:
            
            viewLayerDict[prop.identifier] = getattr(viewLayer, prop.identifier)

    return viewLayerDict



def dictToViewLayer(viewLayer, viewLayerDict):
    
    for key, value in viewLayerDict.items():
        
        if key == 'freestyle_settings':
            
            for freestyleKey, freestyleValue in value.items():
                
                if freestyleKey == 'linesets':
                                        
                    for lineset in freestyleValue:

                        newLineSet = viewLayer.freestyle_settings.linesets.new(lineset['name'])
                        
                        linestyle = newLineSet.linestyle
                        
                        for linesetKey, linesetValue in lineset.items():
                            
                            setattr(newLineSet, linesetKey, linesetValue)
                            
                        #We're assigning the linestyle from the old lineset, meaning the linestyle created 
                        #when the new lineset is created is redundant and needs to be removed    
                        bpy.data.linestyles.remove(linestyle)
                        
                else:
                
                    setattr(viewLayer.freestyle_settings, freestyleKey, freestyleValue)
        
        else:
            
            setattr(viewLayer, key, value)
    
    

def getViewLayersNodes(viewLayerName):
    
    viewLayerNodes = []
    
    for scene in bpy.data.scenes:
    
        if scene.node_tree:
        
            for node in scene.node_tree.nodes:
                
                if node.type == 'R_LAYERS':
                    
                    if node.layer == viewLayerName and node.scene == bpy.context.scene:
            
                        viewLayerNodes.append(node)

    return viewLayerNodes
    


def swapViewLayerNodes(viewLayer1Name, viewLayer2Name):

    viewLayer1Nodes = getViewLayersNodes(viewLayer1Name)
    viewLayer2Nodes = getViewLayersNodes(viewLayer2Name)

    for node in viewLayer1Nodes:
            
        node.layer = viewLayer2Name
         
    for node in viewLayer2Nodes: 
                        
        node.layer = viewLayer1Name



def swapViewLayers(viewLayer1Name, viewLayer2Name):
    
    layers = bpy.context.scene.view_layers
    
    viewLayer1 = layers[viewLayer1Name]
        
    viewLayer1Dict = viewLayerToDict(layers[viewLayer1Name])
    viewLayer2Dict = viewLayerToDict(layers[viewLayer2Name])

    dictToViewLayer(layers[viewLayer1Name], viewLayer2Dict)
    dictToViewLayer(layers[viewLayer2Name], viewLayer1Dict)

    viewLayer1.name = viewLayer2Name



# def swapAnimationData(viewLayer1Name, viewLayer2Name, animationType):
    
#     if animationType == "fcurves":
    
#         animationData = bpy.context.scene.animation_data.action.fcurves    
        
#     elif animationType == "drivers":
    
#         animationData = bpy.context.scene.animation_data.drivers
        
#     for data in animationData:
    
#         dataParts = data.data_path.rpartition('.')
#         dataViewLayer = dataParts[0]
#         dataProperty = dataParts[2]
                    
#         if 'view.layers["' + viewLayer1Name + '"]' == dataViewLayer:
            
#             data.data_path = 'view.layers["' + viewLayer2Name + '"].' + dataProperty
            
#         if 'view.layers["' + viewLayer2Name + '"]' == dataViewLayer:
            
#             data.data_path = 'view.layers["' + viewLayer1Name + '"].' + dataProperty



def moveViewLayer(direction):
    
    layers = bpy.context.scene.view_layers
        
    if direction == "Up" and layers.active_index > 0:
        
        targetLayerIndex = layers.active_index - 1
        
    elif direction == "Up" and layers.active_index == 0:
        
        targetLayerIndex = len(layers) - 1
        
    elif direction == "Down" and layers.active_index < len(layers) - 1:
        
        targetLayerIndex = layers.active_index + 1
        
    elif direction == "Down" and layers.active_index == len(layers) - 1:

        targetLayerIndex = 0        
        
    swapViewLayers(layers[targetLayerIndex].name, layers[layers.active_index].name)
    swapViewLayerNodes(layers[targetLayerIndex].name, layers[layers.active_index].name)
    
    if bpy.context.scene.animation_data:    
    
        swapAnimationData(layers[targetLayerIndex].name, layers[layers.active_index].name, "fcurves")
        swapAnimationData(layers[targetLayerIndex].name, layers[layers.active_index].name, "drivers")
    
    layers.active_index = targetLayerIndex

class VIEWLAYER_UL_viewlayers(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # assert(isinstance(item, bpy.types.SceneRenderLayer)
        layer = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(layer, "name", text="", icon_value=icon, emboss=False)
            layout.prop(layer, "use", text="", index=index)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label("", icon_value=icon)
        
class ViewLayerMoveUp(bpy.types.Operator):
    """Move the current view layer up or down"""
    bl_idname = "scene.view_layer_move_up"
    bl_label = "Move view layer up"

    direction = "Up"

    @classmethod
    def poll(cls, context):
        return len(context.scene.view_layers) > 1

    def execute(self, context):
        moveViewLayer(self.direction)
        return {'FINISHED'}
        
class ViewLayerMoveDown(bpy.types.Operator):
    """Move the current view layer up or down"""
    bl_idname = "scene.view_layer_move_down"
    bl_label = "Move view layer down"

    direction = "Down"

    @classmethod
    def poll(cls, context):
        return len(context.scene.view_layers) > 1

    def execute(self, context):
        moveViewLayer(self.direction)
        return {'FINISHED'}



def ViewLayerMoveButtons(self, context):
    
    layout = self.layout

    scene = context.scene
    rd = scene.render
    vl = scene.view_layers

    row = layout.row()
    col = row.column()
    col.template_list("VIEWLAYER_UL_viewlayers", "", scene, "view_layers", vl, "active_index", rows=2)
    # col.template_list("VIEWLAYER_UL_viewlayers", "", scene, "view_layers", rd.view_layers, "active_index", rows=2)

    col = row.column()
    sub = col.column(align=True)
    sub.operator("scene.view_layer_add", icon='ADD', text="")
    sub.operator("scene.view_layer_remove", icon='REMOVE', text="")
    col.prop(rd, "use_single_layer", icon_only=True)
    
    layout = self.layout
    row = layout.row(align=True)
    operator = row.operator("scene.view_layer_move_up", icon="TRIA_UP", text="")
    operator = row.operator("scene.view_layer_move_down", icon="TRIA_DOWN", text="")
        
        
# append into VIEWLAYER_PT_layer

classes = (
    ViewLayerMoveUp,
    ViewLayerMoveDown,
    VIEWLAYER_UL_viewlayers,
)

def register():
    
    for cl in classes:
        bpy.utils.register_class(cl)
    bpy.types.VIEWLAYER_PT_layer.prepend(ViewLayerMoveButtons)



def unregister():

    for cl in classes:
        bpy.utils.unregister_class(cl)
    bpy.types.VIEWLAYER_PT_layer.remove(ViewLayerMoveButtons)
        


if __name__ == "__main__":
    register()
    