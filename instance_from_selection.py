import bpy
from bpy.types import Operator

bl_info = {
    "name": "Instance from selection",
    "description": "Create an instance from the active object for each selected object copying their transforms",
    "author": "Legigan Jeremy AKA Pistiwique from a kohzale request",
    "version": (0, 0, 1),
    "blender": (2, 78, 0),
    "location": "Properties => Object => Duplication",
    "category": "Object"}


class IFS_OT_instance_from_selection(Operator):
    """ Create an instance from the active object for each selected object copying their transforms """
    bl_idname = "object.ifs_instance_from_selection"
    bl_label = "Instance From Selection"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object is not None and \
               context.selected_objects and \
               context.active_object.type == 'MESH'

    def execute(self, context):
        mainLayer = context.window_manager.ifs_Layer

        mainObj = bpy.context.active_object
        mainLoc = mainObj.location.copy()
        mainRoc = mainObj.rotation_euler.copy()
        mainScale = mainObj.scale.copy()
        selection = bpy.context.selected_objects

        # Placement of the active object at the center of the scene
        mainObj.location = (0, 0, 0)

        # A group assignment operating by selection, we must deselect
        # all the objects and re-select only the mainObj
        bpy.ops.object.select_all(action='DESELECT')
        mainObj.select = True
        bpy.ops.object.rotation_clear(clear_delta=False)

        # Creating new group by naming it with the mainObj name
        newGroup = bpy.data.groups.new(mainObj.name)
        # Assignment of the mainObj to the new group
        bpy.ops.object.group_link(group=newGroup.name)

        # Creating new instance for each selected object
        # Each new instance get the transfomrs of the replaced object
        for obj in selection:
            if obj != mainObj:
                loc = obj.location
                rot = obj.rotation_euler
                scale = obj.scale
            else:
                loc = mainLoc
                rot = mainRoc
                scale = mainScale

            bpy.ops.object.group_instance_add(group=mainObj.name, location=loc)

            newInstance = bpy.context.active_object
            newInstance.rotation_euler = rot
            newInstance.scale = scale
            newInstance.select = False

        # Remove the objects from "selection" except mainObj
        for obj in selection:
            if obj != mainObj:
                bpy.data.objects.remove(obj, do_unlink=True)

        # Clean data meshes
        for meshe in bpy.data.meshes:
            if not meshe.users:
                bpy.data.meshes.remove(meshe, do_unlink=True)

        bpy.context.scene.objects.active = mainObj
        mainObj.select = True
        layer = context.scene.active_layer
        mainObj.layers[mainLayer] = True
        mainObj.layers[layer] = False

        return {"FINISHED"}


class IFS_OT_select_main(Operator):
    """ Select the main from the selected instance """
    bl_idname = "object.ifs_select_main"
    bl_label = "Select Main"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.selected_objects and \
               (context.object.dupli_group or len([idx for idx in range(20) if
                                                   context.active_object.layers[
                                                       idx]]) > 1)

    def execute(self, context):

        actObj = bpy.context.active_object
        dp_group = actObj.dupli_group

        if dp_group:
            main = bpy.data.objects.get(dp_group.name)

            if main:
                for obj in context.scene.objects:
                    obj.select = False

                bpy.context.scene.objects.active = main
                main.select = True

                activeLayer = context.scene.active_layer
                if not main.layers[activeLayer]:
                    main.layers[activeLayer] = True

            return {'FINISHED'}

        objectLayers = [idx for idx in range(20) if actObj.layers[idx]]
        activeLayer = context.scene.active_layer
        for index in objectLayers:
            if index != context.scene.active_layer:
                actObj.layers[index] = True
                actObj.layers[activeLayer] = False
                break

        return {'FINISHED'}


class IFS_OT_make_instance_real(Operator):
    bl_idname = 'object.ifs_make_instance_real'
    bl_label = "Make Real"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object.dupli_group

    def execute(self, context):
        mainObj = bpy.context.active_object

        for obj in bpy.context.selected_objects:
            if obj.dupli_group:
                bpy.context.scene.objects.active = obj
                bpy.ops.object.duplicates_make_real(use_base_parent=True,
                                                    use_hierarchy=True)
                bpy.ops.object.select_hierarchy(direction='CHILD',
                                                extend=False)
                bpy.ops.object.select_hierarchy(direction='PARENT',
                                                extend=False)
                bpy.ops.object.group_unlink()
                bpy.context.object.show_x_ray = True

        bpy.context.scene.objects.active = mainObj

        return {'FINISHED'}


def instance_from_selection_panel(self, context):
    wm = context.window_manager
    layout = self.layout
    split = layout.split()
    col = split.column(align=True)
    row = col.row(align=True)

    row.scale_y = 1.5
    row.operator('object.ifs_instance_from_selection', icon='MOD_ARRAY')
    row.operator('object.ifs_select_main', text="", icon='RESTRICT_SELECT_OFF')
    row = col.row(align=True)
    row.scale_y = 1.5
    row.operator('object.ifs_make_instance_real', text="Make Real",
                 icon='RESTRICT_SELECT_OFF')
    row = col.row(align=True)
    row.label("Main to layer:")
    row.prop(wm, 'ifs_Layer')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.WindowManager.ifs_Layer = bpy.props.IntProperty(
            name="Layer index",
            default=0,
            min=0, max=19,
            description="Layer where the active_object will be send",
            )
    bpy.types.OBJECT_PT_duplication.prepend(instance_from_selection_panel)


def unregister():
    del bpy.types.WindowManager.ifs_Layer
    bpy.types.OBJECT_PT_duplication.remove(instance_from_selection_panel)
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()