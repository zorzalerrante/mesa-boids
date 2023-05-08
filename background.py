import numpy as np
from OpenGL.GL import GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, shaders

from grafica.gpu_tools import prepare_gpu_buffer

vertex_shader = """
#version 330
in vec3 position;
in vec3 color;

out vec3 fragColor;

void main()
{
    fragColor = color;
    gl_Position = vec4(position, 1.0f);
}
"""

fragment_shader = """
#version 330

in vec3 fragColor;
out vec4 outColor;

void main()
{
    outColor = vec4(fragColor, 1.0f);
}
"""


def create_shader_program():
    return shaders.compileProgram(
        shaders.compileShader(vertex_shader, GL_VERTEX_SHADER),
        shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER),
    )


def create_quad():
    vertexData = np.array(
        [
            -1,
            -1,
            0.0,
            1.0,
            204 / 255.0,
            1.0,  # inf izq
            1,
            -1,
            0.0,
            1.0,
            204 / 255.0,
            1.0,  # if der
            1,
            1,
            0.0,
            204 / 255.0,
            1.0,
            1.0,  # sup der
            -1,
            1,
            0.0,
            204 / 255.0,
            1.0,
            1.0,  # sup izq
        ],
        dtype=np.float32,
    )

    indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

    pipeline = create_shader_program()
    return pipeline, prepare_gpu_buffer(
        pipeline, vertexData, indices, normals=False, texture=False, colors=True
    )
