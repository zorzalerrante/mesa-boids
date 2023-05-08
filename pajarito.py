import os
from collections import defaultdict, deque
from ctypes.wintypes import SIZE
from itertools import chain
from multiprocessing.spawn import prepare

import numpy as np
import pyglet
import pyglet.graphics as pygr
import trimesh
from OpenGL.GL import *
from OpenGL.GL import shaders
from PIL import Image

import grafica.transformations as tr
from boid_flockers.model import BoidFlockers
from grafica.gpu_tools import trimesh_to_gpu
from grafica.scene_graph import SceneGraphNode, find_node
from grafica.shape import Shape

vertex_shader = """
#version 330

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 transform;

in vec3 position;
in vec2 texCoords;

out vec2 outTexCoords;

void main()
{
    vec4 vertexPos = model * vec4(position, 1.0);
    gl_Position = projection * view * transform * vertexPos;
    outTexCoords = texCoords;
}
"""

fragment_shader = """
#version 330

in vec2 outTexCoords;

out vec4 outColor;

uniform sampler2D samplerTex;

void main()
{
    vec4 texel = texture(samplerTex, outTexCoords);
    if (texel.a < 0.5)
        discard;
    outColor = texel;
}
"""


class Pajarito(Shape):
    def __init__(self, model_path, *args, **kwargs):
        super().__init__(vertex_shader, fragment_shader)

        self.bird = trimesh.load(model_path)

        self.gpu_birds = trimesh_to_gpu(self.bird, self.shader_program)

        self.centroid = self.bird.centroid
        print(self.centroid)

        self.model_transform = tr.matmul(
            [
                tr.translate(*(self.centroid)),
                tr.rotationZ(np.deg2rad(-90)),
                tr.rotationX(np.deg2rad(90)),
                tr.rotationY(np.deg2rad(180)),
                tr.scale(15, 15, 15),
                tr.translate(*(-self.centroid)),
            ]
        )

    def setup_program(self, view_matrix, projection_matrix):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glEnable(GL_DEPTH_TEST)

        # esto activa la transparencia de la textura.
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glUseProgram(self.shader_program)

        glUniformMatrix4fv(
            glGetUniformLocation(self.shader_program, "view"), 1, GL_TRUE, view_matrix
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.shader_program, "projection"),
            1,
            GL_TRUE,
            projection_matrix,
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.shader_program, "model"),
            1,
            GL_TRUE,
            self.model_transform,
        )

    def draw(self, *params, **kwargs):
        # glUniformMatrix4fv(
        #     glGetUniformLocation(self.shader_program, "transform"),
        #     1,
        #     GL_TRUE,
        #     transform,
        # )

        for shape in self.gpu_birds.values():
            glBindVertexArray(shape["vao"])
            glBindTexture(GL_TEXTURE_2D, shape["texture"])
            glDrawElements(GL_TRIANGLES, shape["size"], GL_UNSIGNED_INT, None)
            glBindVertexArray(0)

        glDisable(GL_BLEND)

