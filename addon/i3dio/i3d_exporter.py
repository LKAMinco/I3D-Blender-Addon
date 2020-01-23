#!/usr/bin/env python3

"""
    ##### BEGIN GPL LICENSE BLOCK #####
  This program is free software; you can redistribute it and/or
  modify it under the terms of the GNU General Public License
  as published by the Free Software Foundation; either version 2
  of the License, or (at your option) any later version.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software Foundation,
  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 ##### END GPL LICENSE BLOCK #####
"""
from __future__ import annotations  # Enables python 4.0 annotation typehints fx. using the class itself as a typehint to itself
import sys
# Old exporter used cElementTree for speed, but it was deprecated to compatibility status in python 3.3
import xml.etree.ElementTree as ET  # Technically not following pep8, but this is the naming suggestion from the module
import bpy


# Exporter is a singleton
class Exporter:

    def __init__(self, filepath: str):
        self._scene_graph = SceneGraph()
        self._export_only_selection = False
        self._filepath = filepath

        self._generate_scene_graph()
        self._xml_build_structure()

        #self._xml_parse_from_blender()
        #self._xml_export_to_file()

    def _generate_scene_graph(self):
        for obj in bpy.context.selected_objects:
            # Objects directly in the scene only has the 'Master Collection' in the list,
            # which disappears once the object is added to any other collection
            if bpy.context.scene.collection in obj.users_collection and obj.parent is None:
                print(f"{obj.name!r} is at scene root")

    def _generate_scene_graph_item(self, blender_object, parent):
        pass

    def _xml_build_structure(self) -> None:
        """Builds the i3d file conforming to the standard specified at
        https://gdn.giants-software.com/documentation_i3d.php
        """
        self._tree = ET.Element('i3D')  # Create top level element
        self._tree.set('name', bpy.path.display_name_from_filepath(self._filepath))  # Name attribute

        # Xml scheme attributes as required by the i3d standard, even though most of the links are dead.
        self._tree.set('version', "1.6")
        self._tree.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        self._tree.set('xsi:noNamespaceSchemaLocation', "http://i3d.giants.ch/schema/i3d-1.6.xsd")

        # Asset export: Currently just a notice of which tool was used for generating the file
        element = ET.SubElement(self._tree, 'Asset')
        element = ET.SubElement(element, 'Export')
        element.set('program', 'Blender Exporter (Community)')
        element.set('version', sys.modules['i3dio'].bl_info.get('version'))  # Fetch version directly from bl_info

        # File export: References to external files such as images for materials (diffuse, normals etc.)
        ET.SubElement(self._tree, 'Files')

        # Material export: List of all materials used in the project
        ET.SubElement(self._tree, 'Materials')

        # Shapes export: All the shape data in the form of vertices and triangles. This section takes up a lot of space
        # and it would be preferable to export to an external shapes file (Giants Engine can do it by a binary save)
        ET.SubElement(self._tree, 'Shapes')

        # Dynamics export: Particle systems
        ET.SubElement(self._tree, 'Dynamics')

        # Scenegraph export: The entire scenegraph structure, with references to light, cameras, transforms and shapes
        ET.SubElement(self._tree, 'Scene')

        # Animation export: Animation sets with keyframes
        ET.SubElement(self._tree, 'Animation')

        # User attributes export: User generated attributes that might be used in scripts etc.
        ET.SubElement(self._tree, 'UserAttributes')

    # def _xml_parse_from_blender(self):
    #
    #     # Build a list of objects that should be used to build the scenegraph
    #
    #     #for obj in bpy.context.selected_objects:
    #
    #     for obj in bpy.context.selected_objects:
    #         print(f"{obj.name!r}has type {obj.type!r}")
    #         print(f"Instanced? {obj.is_instancer}")
    #         if obj.parent is None:
    #             print(f"{obj.name!r} has no parent")
    #             if obj.type == 'MESH':
    #                 pass
    #             if obj.type == 'EMPTY':
    #                 print(obj.instance_collection)
    #         else:
    #             print(f"{obj.name!r} has parent {obj.parent.name!r}")

    def _xml_export_to_file(self) -> None:

        self._indent(self._tree)

        try:
            ET.ElementTree(self._tree).write(self._filepath, xml_declaration=True, encoding='iso-8859-1', method='xml')
            print(f"Exported to {self._filepath}")
        except Exception as exception:  # A bit slouchy exception handling. Should be more specific and not catch all
            print(exception)

    @staticmethod
    def _xml_write_int(element: ET.Element, attribute: str, value: int) -> None:
        """Writes the attribute into the element with formatting for ints"""
        element.set(attribute, f"{value:d}")

    @staticmethod
    def _xml_write_float(element: ET.Element, attribute: str, value: float) -> None:
        """Writes the attribute into the element with formatting for floats"""
        element.set(attribute, f"{value:.7f}")

    @staticmethod
    def _xml_write_bool(element: ET.Element, attribute: str, value: bool) -> None:
        """Writes the attribute into the element with formatting for booleans"""
        element.set(attribute, f"{value!s}".lower())

    @staticmethod
    def _xml_write_string(element: ET.Element, attribute: str, value: str) -> None:
        """Writes the attribute into the element with formatting for strings"""
        element.set(attribute, value)

    @staticmethod
    def _indent(elem: ET.Element, level: int = 0) -> None:
        """
        Used for pretty printing the xml since etree does not indent elements and keeps everything in one continues
        string and since i3d files are supposed to be human readable, we need indentation. There is a patch for
        pretty printing on its way in the standard library, but it is not available until python 3.9 comes around.

        The module 'lxml' could also be used since it has pretty-printing, but that would introduce an external
        library dependency for the addon.

        The source code from this solution is taken from http://effbot.org/zone/element-lib.htm#prettyprint

        It recursively checks every element and adds a newline + space indents to the element to make it pretty and
        easily readable. This technically changes the xml, but the giants engine does not seem to mind the linebreaks
        and spaces, when parsing the i3d file.
        """
        indents = '\n' + level * '  '
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indents + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = indents
            for elem in elem:
                Exporter._indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = indents
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indents


class SceneGraph(object):

    class Node(object):
        id = 0  # NodeID shared between all nodes and incremented upon new node creation

        def __init__(self, blender_object: [bpy.types.Object] = None, parent: SceneGraph.Node = None):
            self.children = {}
            self.blender_object = blender_object
            self.id = SceneGraph.Node.id
            SceneGraph.Node.id += 1  # Increment the ID every time a node is created
            self.parent = parent

        def add_child(self, node: SceneGraph.Node):
            self.children[node.id] = node

        def remove_child(self, node: SceneGraph.Node):
            del self.children[node.id]

    def __init__(self):
        self._nodes = {}
        self._shapes = {}
        self._materials = {}
        self._files = {}
        self._nodes["ROOT"] = SceneGraph.Node(None)

    def add_node(self, blender_object, parent):
        self.ids['node'] += 1

