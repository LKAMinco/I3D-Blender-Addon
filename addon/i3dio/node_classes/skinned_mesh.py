"""
A lot of classes in this file is purely to have different classes for different objects that are functionally the same,
but it helps with debugging big trees and seeing the structure.
"""
from __future__ import annotations
from typing import (Union, Dict, List, Type, OrderedDict, Optional)
import mathutils
import bpy

from . import node
from .node import (TransformGroupNode, SceneGraphNode)
from .shape import (ShapeNode, EvaluatedMesh)
from ..i3d import I3D


class SkinnedMeshBoneNode(TransformGroupNode):
    def __init__(self, id_: int, bone_object: bpy.types.Bone,
                 i3d: I3D, parent: SceneGraphNode):
        super().__init__(id_=id_, empty_object=bone_object, i3d=i3d, parent=parent)

    @property
    def _transform_for_conversion(self) -> mathutils.Matrix:

        if self.blender_object.parent is None:
            # The bone is parented to the armature directly, and therefor should just use the matrix_local which is in
            # relation to the armature anyway.
            bone_transform = self.blender_object.matrix_local
        else:
            # To find the transform of the bone, we take the inverse of its parents transform in armature space and
            # multiply that with the bones transform in armature space. The new 4x4 matrix gives the position and
            # rotation in relation to the parent bone (of the head, that is)
            bone_transform = self.blender_object.parent.matrix_local.inverted() @ self.blender_object.matrix_local

        conversion_matrix = self.i3d.conversion_matrix @ bone_transform @ self.i3d.conversion_matrix.inverted()

        return conversion_matrix


class SkinnedMeshRootNode(TransformGroupNode):
    def __init__(self, id_: int, armature_object: bpy.types.Armature,
                 i3d: I3D, parent: Union[SceneGraphNode, None] = None):
        # The skinBindID essentially, but mapped with the bone names for easy reference. An ordered dict is important
        # but dicts should be ordered going forwards in python
        self.bones: List[SkinnedMeshBoneNode] = list()
        self.bone_mapping: Dict[str, int] = {}
        # To determine if we just added the armature through a modifier lookup or knows its position in the scenegraph
        self.is_located = False
        super().__init__(id_=id_, empty_object=armature_object, i3d=i3d, parent=parent)
        for bone in armature_object.data.bones:
            if bone.parent is None:
                self._add_bone(bone, self)

        self.skin_bind_ids = ""
        for bone in self.bones:
            self.skin_bind_ids += f"{bone.id:d} "
        self.skin_bind_ids = self.skin_bind_ids[:-1]

    def _add_bone(self, bone_object: bpy.types.Bone, parent: Union[SkinnedMeshBoneNode, SkinnedMeshRootNode]):
        """Recursive function for adding a bone along with all of its children"""
        self.logger.debug(f"Exporting Bone: '{bone_object.name}', head: {bone_object.head}, tail: {bone_object.tail}")
        self.bones.append(self.i3d.add_bone(bone_object, parent))
        self.bone_mapping[bone_object.name] = len(self.bones) - 1

        for child_bone in bone_object.children:
            self._add_bone(child_bone, self.bones[-1])


class SkinnedMeshShapeNode(ShapeNode):
    def __init__(self, id_: int, skinned_mesh_object: [bpy.types.Object, None], i3d: I3D,
                 parent: [SceneGraphNode or None] = None):
        for modifier in skinned_mesh_object.modifiers:
            if modifier.type == 'ARMATURE':
                self.armature_node = i3d.add_armature(modifier.object)
        super().__init__(id_=id_, mesh_object=skinned_mesh_object, i3d=i3d, parent=parent)

    def add_shape(self):
        self.shape_id = self.i3d.add_shape(EvaluatedMesh(self.i3d, self.blender_object),
                                           bone_mapping=self.armature_node.bone_mapping)
        self.xml_elements['IndexedTriangleSet'] = self.i3d.shapes[self.shape_id].element

    def populate_xml_element(self):
        super().populate_xml_element()
        self._write_attribute('skinBindNodeIds', self.armature_node.skin_bind_ids)