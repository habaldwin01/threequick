import pygame
import numpy as np
import math
from io import BytesIO
from threequick import CameraContext, Object3d, Cube, Sphere, Line3d


window = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
pygame.display.set_caption("threequick test")
done = False
renderable_objects = []


tc = Cube(0.2)
# pitch  roll   yaw
# x      y      z
#tc.set_rotation(0,0,0)
#tc.set_position(0,0,0)
tc.set_rotation(30,10,60)
tc.set_position(1,0,0)
renderable_objects.append(tc)

sp = Sphere(16, 6+1, 1)
renderable_objects.append(sp)


# Set up lines for gizmo
gizmo_stroke_width = 3
gizmo_size = 20
gizmo_edge_dist = 50
gizmo_x = Line3d([[0,0,0], [0,0,0]], (255,0,0), stroke_width = gizmo_stroke_width, end_arrow = gizmo_stroke_width)
renderable_objects.append(gizmo_x)
gizmo_y = Line3d([[0,0,0], [0,0,0]], (0,255,0), stroke_width = gizmo_stroke_width, end_arrow = gizmo_stroke_width)
renderable_objects.append(gizmo_y)
gizmo_z = Line3d([[0,0,0], [0,0,0]], (0,0,255), stroke_width = gizmo_stroke_width, end_arrow = gizmo_stroke_width)
renderable_objects.append(gizmo_z)

#point_cloud = PointCloud()
#renderable_objects.append(point_cloud)

#point_cloud.add_point([0,0.25,0.25], [0,255,0])

cam_dist = 3
gizmo_dist = -cam_dist + 1

screen_size = (1280, 720)
camera_context = CameraContext([0,-cam_dist,0], [70,0,30], 90, screen_size)
camera_context.position[0] = (math.sin(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
camera_context.position[1] = (math.cos(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
camera_context.position[2] = math.cos(math.radians(camera_context.rotation[0])) * -cam_dist

cube_angle = 0

pygame.init()

last_ticks = pygame.time.get_ticks()

while not done:
    current_ticks = pygame.time.get_ticks()
    camera_context.set_screen_size(window.get_width()/2, window.get_height()/2)

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
    #tc.set_position(0,0,0)

    # Slow rotation of camera
    #camera_context.rotation[2] += (last_ticks - current_ticks) / 80


    # Calculate camera position based off angle so it always points at 0,0,0
    camera_context.position[0] = (math.sin(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
    camera_context.position[1] = (math.cos(math.radians(camera_context.rotation[2])) * -cam_dist) * math.sin(math.radians(camera_context.rotation[0]))
    camera_context.position[2] = math.cos(math.radians(camera_context.rotation[0])) * -cam_dist
    
    # Push gizmo to top right corner
    gizmo_origin = [(math.sin(math.radians(camera_context.rotation[2])) * -gizmo_dist) * math.sin(math.radians(camera_context.rotation[0])),
                    (math.cos(math.radians(camera_context.rotation[2])) * -gizmo_dist) * math.sin(math.radians(camera_context.rotation[0])),
                    math.cos(math.radians(camera_context.rotation[0])) * -gizmo_dist]
    base_ssd = [camera_context.screen_size[0] / 2,-camera_context.screen_size[1] / 2]
    gizmo_ssd = [base_ssd[0] - gizmo_edge_dist, base_ssd[1] + gizmo_edge_dist]
    gizmo_scale = gizmo_size / camera_context.screen_size[0]
    gizmo_x.screen_space_displace = gizmo_ssd
    gizmo_y.screen_space_displace = gizmo_ssd
    gizmo_z.screen_space_displace = gizmo_ssd
    gizmo_x.vertices = [gizmo_origin,[gizmo_origin[0] + gizmo_scale, gizmo_origin[1], gizmo_origin[2]]]
    gizmo_y.vertices = [gizmo_origin,[gizmo_origin[0], gizmo_origin[1] + gizmo_scale, gizmo_origin[2]]]
    gizmo_z.vertices = [gizmo_origin,[gizmo_origin[0], gizmo_origin[1], gizmo_origin[2] + gizmo_scale]]


    last_ticks = current_ticks

    camera_context.update_screenspace()
    
    camera_context.surface.clear()
    
    for ro in renderable_objects:
        camera_context.surface.draw(ro)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
            
            
    svg_drawing = camera_context.surface.to_drawsvg_obj()
    svg_drawing.save_svg("frame.svg")
    
    raster = svg_drawing.rasterize()
    binary_buffer = BytesIO(raster.png_data)
    raster_surface = pygame.image.load(binary_buffer, "frame.png")
    raster_surface = pygame.transform.scale(raster_surface, (window.get_width(), window.get_height()))
    pygame.draw.rect(window, (0, 0, 0), (0, 0, window.get_width(), window.get_height()))
    window.blit(raster_surface, window.get_rect())

    pygame.display.flip()

exit()
