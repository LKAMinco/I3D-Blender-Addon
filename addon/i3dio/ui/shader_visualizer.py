import logging
from os import path

import bpy
from bpy.props import (
    EnumProperty
)
from bpy.types import (Panel, Operator)

classes = []


def register(cls):
    classes.append(cls)
    return cls


def print(*args):
    msg = ' '.join(map(str, args))
    logging.log(logging.WARNING, msg)


@register
class I3D_IO_PT_MatVisualizer(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_label = "Shader Visualizer (for now just vehicleShader.xml)"
    bl_context = 'material'
    bl_parent_id = 'I3D_IO_PT_shader'
    bl_default_closed = True

    def draw(self, context):
        layout = self.layout
        layout.operator('i3dio.material_visualizer', text='Prepare Material', icon='SHADERFX').action = 'SET_UP'
        split = layout.split(factor=0.5)
        split.operator('i3dio.material_visualizer', text='Update Material', icon='SHADERFX').action = 'UPDATE_MAT'
        split.operator('i3dio.material_visualizer', text='Update Shader', icon='SHADERFX').action = 'UPDATE_SHADER'


@register
class I3D_IO_PT_MatVisProperties(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_label = "Shader Control Properties"
    bl_context = 'material'
    bl_parent_id = 'I3D_IO_PT_MatVisualizer'
    bl_default_closed = True

    def draw(self, context):
        layout = self.layout
        layout.label(text='Shader Variation Properties')


@register
class I3D_IO_OT_MatVisualizer(Operator):
    bl_idname = 'i3dio.material_visualizer'
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER'}

    action: EnumProperty(items=[
        ('SET_UP', 'Visualize Material', 'Load shader into shader editor and prepare all material connections'),
        ('UPDATE_MAT', 'Update Material', 'Update material shader from shader variation properties'),
        ('UPDATE_SHADER', 'Update Shader', 'Update the shader variation from the material shader')
    ])

    @classmethod
    def poll(cls, context):
        return validate_shader()

    @classmethod
    def description(cls, context, properties) -> str:
        if properties.action == 'SET_UP':
            return 'Load shader into shader editor and prepare all material connections'
        elif properties.action == 'UPDATE_MAT':
            return 'Update material shader from shader variation properties'
        elif properties.action == 'UPDATE_SHADER':
            return 'Update the shader variation from the material shader'

    def execute(self, context):
        if 'FS25_VehicleShader' not in bpy.data.node_groups:
            if context.active_object is not None:
                if context.active_object.mode == 'EDIT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                    import_shader()
                    bpy.ops.object.mode_set(mode='EDIT')
                else:
                    import_shader()

        return {'FINISHED'}


def import_shader():
    library = path.abspath(path.join(path.dirname(__file__), 'shaders.blend'))
    filepath = path.join(library, 'NodeTree', 'FS25_VehicleShader')
    directory = path.join(library, 'NodeTree')
    bpy.ops.wm.append(
        filepath=filepath,
        filename='FS25_VehicleShader',
        directory=directory
    )


def validate_shader():
    source_path = bpy.context.object.active_material.i3d_attributes.source
    if source_path != '':
        valid_shader_variations = 'vehicleShader.xml'  # in the future, also other shaders
        file_name = path.basename(source_path)
        return file_name == valid_shader_variations
    return False


def validate_mat_shader():
    if bpy.context.object.active_material is not None:
        return 'FS25_VehicleShader' in bpy.context.object.active_material.node_tree.nodes
    return False


def set_up_mat():
    pass


def update_mat_from_shader():
    pass


def update_shader_from_mat():
    pass


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
