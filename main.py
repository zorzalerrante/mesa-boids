from pathlib import Path

import numpy as np
import pyglet
from OpenGL.GL import (
    GL_DEPTH_TEST,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    glBindVertexArray,
    glClearColor,
    glDisable,
    glDrawElements,
    glEnable,
    glUseProgram,
)

import grafica.transformations as tr
from background import create_quad
from boid_flockers.model import BoidFlockers
from grafica.scene_graph import SceneGraphNode, draw_scenegraph_node, find_node
from pajarito_render import PajaritoRender

program_state = {
    "paused": False,
    "bird_camera": False,
    "view_matrix": None,
    "projection_matrix": None,
}


def main():
    window = pyglet.window.Window(width=1024, height=768)

    flock = BoidFlockers(
        60,
        width=640,
        height=480,
        speed=0.75,
        vision=100,
        separation=20,
        cohere=0.001,
        separate=0.1,
        match=0.001,
    )

    bird_path = Path("assets") / "zorzal2.obj"
    renderer = PajaritoRender(bird_path)

    bg_shader, bg_quad = create_quad()

    graph = SceneGraphNode("world")

    for boid, name in flock.iter_agents():
        bird = SceneGraphNode(name)
        bird.childs = [renderer.gpu_birds]
        graph.childs.append(bird)

    def tick(time):
        if not program_state["paused"]:
            flock.step()

            for boid, name in flock.iter_agents():
                angle = np.arctan2(boid.velocity[1], boid.velocity[0])

                node = find_node(graph, name)
                node.transform = tr.matmul(
                    [
                        tr.translate(boid.pos[0], boid.pos[1], 0.0),
                        # tr.translate(*(self.centroid * 20)),
                        # tr.rotationZ(np.deg2rad(-90)),
                        tr.rotationZ(angle),
                        tr.translate(*(-renderer.centroid * 15)),
                    ]
                )

        program_state["view_matrix"] = view_transform(program_state["bird_camera"])

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.V:
            program_state["bird_camera"] = not program_state["bird_camera"]

        if symbol == pyglet.window.key.P:
            program_state["paused"] = not program_state["paused"]

    @window.event
    def on_draw():
        glClearColor(0.85, 0.85, 0.85, 1.0)
        window.clear()

        glDisable(GL_DEPTH_TEST)
        glUseProgram(bg_shader)
        glBindVertexArray(bg_quad["vao"])
        glDrawElements(GL_TRIANGLES, bg_quad["size"], GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        glEnable(GL_DEPTH_TEST)

        renderer.setup_program(
            program_state["view_matrix"], program_state["projection_matrix"]
        )

        draw_scenegraph_node(graph, renderer, "transform")

    def view_transform(bird_camera):
        if not bird_camera:
            viewPos = np.array([320, 240, 600])
            view = tr.lookAt(viewPos, np.array([320, 240, 0]), np.array([0, 1, 0]))
        else:
            boid = next(iter(flock.iter_agents(index=False)))
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

        return view

    program_state["view_matrix"] = view_transform(program_state["bird_camera"])
    program_state["projection_matrix"] = tr.perspective(
        60, float(window.width) / float(window.height), 1, 1000
    )

    pyglet.clock.schedule_interval(tick, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
