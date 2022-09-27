import pyglet

from boid_flockers.model import BoidFlockers
from pajarito_render import PajaritoRender
from background import create_quad
from OpenGL.GL import glClearColor, glEnable, glDisable, GL_DEPTH_TEST, glUseProgram, glBindVertexArray, glDrawElements, GL_TRIANGLES, GL_UNSIGNED_INT

from pathlib import Path

program_params = {
    'paused': False,
    'bird_camera': False
}

def main():
    window = pyglet.window.Window(width=1024, height=768)

    
    flock = BoidFlockers(60, width=640, height=480, speed=0.75, vision=100, separation=20, cohere=0.001, separate=0.1, match=0.001)

    bird_path = Path('assets') / 'zorzal2.obj'
    renderer = PajaritoRender(bird_path)


    bg_shader, bg_quad = create_quad()

    def tick(time):
        if not program_params['paused']:
            flock.step()


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
        renderer.draw(flock, bird_camera=program_params['bird_camera'])

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.V:
            program_params['bird_camera'] = not program_params['bird_camera']

        if symbol == pyglet.window.key.P:
            program_params['paused'] = not program_params['paused']

    pyglet.clock.schedule_interval(tick,1/60)
    pyglet.app.run()


if __name__ == "__main__":
    main()