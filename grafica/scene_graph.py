# coding=utf-8
"""A simple scene graph class and functionality"""

from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import grafica.transformations as tr

__author__ = "Daniel Calderon"
__license__ = "MIT"


class SceneGraphNode:
    """
    A simple class to handle a scene graph
    Each node represents a group of objects
    Each leaf represents a basic figure (GPUShape)
    To identify each node properly, it MUST have a unique name
    """

    def __init__(self, name):
        self.name = name
        self.transform = tr.identity()
        self.childs = []

    def clear(self):
        """Freeing GPU memory"""

        for child in self.childs:
            child.clear()


def find_node(node, name):
    # The name was not found in this path
    if isinstance(node, dict):
        return None

    # This is the requested node
    if node.name == name:
        return node

    # All childs are checked for the requested name
    for child in node.childs:
        foundNode = find_node(child, name)
        if foundNode != None:
            return foundNode

    # No child of this node had the requested name
    return None


def find_transform(node, name, parentTransform=tr.identity()):
    # The name was not found in this path
    if isinstance(node, dict):
        return None

    newTransform = np.matmul(parentTransform, node.transform)

    # This is the requested node
    if node.name == name:
        return newTransform

    # All childs are checked for the requested name
    for child in node.childs:
        foundTransform = find_transform(child, name, newTransform)
        if isinstance(foundTransform, (np.ndarray, np.generic)):
            return foundTransform

    # No child of this node had the requested name
    return None


def find_position(node, name, parentTransform=tr.identity()):
    foundTransform = find_transform(node, name, parentTransform)

    if isinstance(foundTransform, (np.ndarray, np.generic)):
        zero = np.array([[0, 0, 0, 1]], dtype=np.float32).T
        foundPosition = np.matmul(foundTransform, zero)
        return foundPosition

    return None


def draw_scenegraph_node(node, pipeline, transformName, parentTransform=tr.identity()):
    # assert(isinstance(node, SceneGraphNode))

    # Composing the transformations through this path
    newTransform = np.matmul(parentTransform, node.transform)

    # If the child node is a leaf, it should be a GPUShape.
    # Hence, it can be drawn with drawCall
    if len(node.childs) == 1 and isinstance(node.childs[0], dict):
        leaf = node.childs[0]
        glUniformMatrix4fv(
            glGetUniformLocation(pipeline.shader_program, transformName),
            1,
            GL_TRUE,
            newTransform,
        )
        pipeline.draw(leaf)

    # If the child node is not a leaf, it MUST be a SceneGraphNode,
    # so this draw function is called recursively
    else:
        for child in node.childs:
            draw_scenegraph_node(child, pipeline, transformName, newTransform)
