import os
from collections import defaultdict
from ctypes.wintypes import SIZE
from multiprocessing.spawn import prepare

import numpy as np
import pyglet.graphics as pygr
import trimesh
from OpenGL.GL import *
from OpenGL.GL import shaders
from PIL import Image

import transformations as tr
from boid_flockers.model import BoidFlockers
from gl_tools import prepare_gpu_buffer, texture_setup

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


class PajaritoRender:
    def __init__(self, model_path, *args, **kwargs):
        self.pipeline = shaders.compileProgram(
            shaders.compileShader(vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        self.bird = trimesh.load(model_path)

        self.gpu_birds = {}
        for mesh_name, mesh in self.bird.geometry.items():
            mesh_parts = trimesh.rendering.mesh_to_vertexlist(mesh)
            mesh_vertex_data = np.hstack(
                [
                    np.array(mesh_parts[4][1]).reshape(-1, 3),
                    np.array(mesh_parts[5][1]).reshape(-1, 3),
                    np.array(mesh_parts[6][1]).reshape(-1, 2),
                ]
            ).reshape(1, -1)
            mesh_vertex_data = np.array(np.squeeze(mesh_vertex_data))
            print(mesh_vertex_data.shape)
            print(mesh_vertex_data[0:10])
            # mesh_indices = list(zip(mesh_parts[3][0::3], mesh_parts[3][1::3], mesh_parts[3][2::3]))
            mesh_indices = mesh_parts[3]
            print(mesh_indices[0:10])
            self.gpu_birds[mesh_name] = prepare_gpu_buffer(
                self.pipeline, mesh_vertex_data, mesh_indices
            )
            print(mesh_name, mesh_parts[4][0], mesh_parts[5][0], mesh_parts[6][0])

            self.gpu_birds[mesh_name]["texture"] = texture_setup(
                mesh.visual.material.image, GL_REPEAT, GL_REPEAT, GL_LINEAR, GL_LINEAR
            )
            print(mesh_name, self.gpu_birds[mesh_name])

        self.centroid = self.bird.centroid
        print(self.centroid)

        # Setting uniforms that will NOT change on each iteration
        glUseProgram(self.pipeline)

        projection = tr.perspective(60, float(1024) / float(768), 1, 1000)
        glUniformMatrix4fv(
            glGetUniformLocation(self.pipeline, "projection"),
            1,
            GL_TRUE,
            projection,
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.pipeline, "model"),
            1,
            GL_TRUE,
            tr.matmul(
                [
                    tr.translate(*(self.centroid)),
                    tr.rotationZ(np.deg2rad(-90)),
                    tr.rotationX(np.deg2rad(90)),
                    tr.rotationY(np.deg2rad(180)),
                    tr.scale(15, 15, 15),
                    tr.translate(*(-self.centroid)),
                ]
            ),
        )

        self.focus_on_bird = False

    def draw(self, world: BoidFlockers, bird_camera: bool=False):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # esto activa la transparencia de la textura.
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if not bird_camera:
            viewPos = np.array([320, 240, 600])
            view = tr.lookAt(viewPos, np.array([320, 240, 0]), np.array([0, 1, 0]))
        else:
            boid = next(iter(world.space._agent_to_index.keys()))
            bird_position = np.array([boid.pos[0], boid.pos[1], 0, 1])
            angle = np.arctan2(boid.velocity[1], boid.velocity[0])

            camera_transform = tr.matmul(
                [
                    tr.rotationZ(angle),
                    tr.translate(-25, 0, 25),
                    tr.rotationZ(-angle),
                ]
            )

            look_at_transform = tr.matmul(
                [
                    tr.rotationZ(angle),
                    tr.translate(20, 0, 0),
                    tr.rotationZ(-angle),
                ]
            )

            camera_position = np.matmul(camera_transform, bird_position)
            look_at_position = np.matmul(look_at_transform, bird_position)

            view = tr.lookAt(
                camera_position[0:3],
                look_at_position[0:3],
                np.array([0, 0, 1]),
            )

        glUseProgram(self.pipeline)

        glUniformMatrix4fv(
            glGetUniformLocation(self.pipeline, "view"), 1, GL_TRUE, view
        )

        

        for boid in world.space._agent_to_index.keys():
            if boid is None:
                continue

            angle = np.arctan2(boid.velocity[1], boid.velocity[0])

            glUniformMatrix4fv(
                glGetUniformLocation(self.pipeline, "transform"),
                1,
                GL_TRUE,
                tr.matmul(
                    [
                        tr.translate(boid.pos[0], boid.pos[1], 0.0),
                        # tr.translate(*(self.centroid * 20)),
                        # tr.rotationZ(np.deg2rad(-90)),
                        tr.rotationZ(angle),
                        tr.translate(*(-self.centroid * 15)),
                    ]
                ),
            )

            for shape in self.gpu_birds.values():
                glBindVertexArray(shape["vao"])
                glBindTexture(GL_TEXTURE_2D, shape["texture"])
                glDrawElements(GL_TRIANGLES, shape["size"], GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
                # shape.draw(GL_TRIANGLES)
