from OpenGL.GL import GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, shaders


class Shape:
    def __init__(self, vertex_shader, fragment_shader, *args, **kwargs):
        self.shader_program = shaders.compileProgram(
            shaders.compileShader(vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        self.transform_name = "transform"

    def setup_program(self, view_matrix, projection_matrix):
        pass

    def draw(self, *params, **kwargs):
        pass
