import pygame
import numpy as np
import math
from threequick import CameraContext, Object3d, Cube, Sphere, PointCloud


window = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
pygame.display.set_caption("threequick test")
done = False
renderable_objects = []


tc = Cube(0.2)
# pitch  roll   yaw
# x      y      z
tc.set_rotation(30,10,60)
tc.set_position(1,0,0)
renderable_objects.append(tc)

sp = Sphere(16, 6+1, 1)
renderable_objects.append(sp)

#point_cloud = PointCloud()
#renderable_objects.append(point_cloud)

#point_cloud.add_point([0,0.25,0.25], [0,255,0])

cam_dist = 2

camera_context = CameraContext([0,-cam_dist,0], [70,0,30], 90, window)
camera_context.position[0] = (math.sin(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
camera_context.position[1] = (math.cos(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
camera_context.position[2] = math.cos(math.radians(camera_context.rotation[0])) * -cam_dist

cube_angle = 0

pygame.init()

last_ticks = pygame.time.get_ticks()

while not done:
    current_ticks = pygame.time.get_ticks()

    pygame.draw.rect(window, (0, 0, 0), (0, 0, window.get_width(), window.get_height()))

    mx, my = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

    left_button, middle_button, right_button = pygame.mouse.get_pressed()
    if not left_button:
        last_rc_pos = (mx, my)


    if left_button:
        camera_context.rotation[0] -= (my - last_rc_pos[1]) * 0.2
        if camera_context.rotation[0] > 180:
            camera_context.rotation[0] = 180
        if camera_context.rotation[0] < 0:
            camera_context.rotation[0] = 0
        smx = (math.sin(math.radians(camera_context.rotation[0]))) + 0.5
        camera_context.rotation[2] -= (mx - last_rc_pos[0]) * 0.2 / smx
        last_rc_pos = (mx, my)


    orbital_period_s = 8
    cube_angle = ((pygame.time.get_ticks() / 1000) / orbital_period_s) * 360

    tc.set_rotation(30,10,60 + cube_angle)
    tc.set_position(math.sin(math.radians(cube_angle)),-math.cos(math.radians(cube_angle)),0)

    # Slow rotation of camera
    #camera_context.rotation[2] += (last_ticks - current_ticks) / 80


    # Calculate camera position based off angle so it always points at 0,0,0
    camera_context.position[0] = (math.sin(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
    camera_context.position[1] = (math.cos(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
    camera_context.position[2] = math.cos(math.radians(camera_context.rotation[0])) * -cam_dist


    last_ticks = current_ticks

    camera_context.update_screenspace()
    for ro in renderable_objects:
        ro.draw(camera_context)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    pygame.display.flip()

exit()
