import pygame
import pygame.font
import numpy as np
import math
import random
from typing import Optional, Union

pygame.font.init()
sans_font = pygame.font.Font(pygame.font.get_default_font(), 36)

def transform_3d_point_4x4_mat(matrix, point):
    # Convert to homogeneous coordinates
    x = point[0] * matrix[0][0] + point[1] * matrix[0][1] + point[2] * matrix[0][2] + matrix[0][3]
    y = point[0] * matrix[1][0] + point[1] * matrix[1][1] + point[2] * matrix[1][2] + matrix[1][3]
    z = point[0] * matrix[2][0] + point[1] * matrix[2][1] + point[2] * matrix[2][2] + matrix[2][3]
    w = point[0] * matrix[3][0] + point[1] * matrix[3][1] + point[2] * matrix[3][2] + matrix[3][3]

    # Convert back from homogeneous coordinates
    if w != 0:
        return [x / w, y / w, z / w]
    else:
        return [x, y, z]

def pry_rot_to_4x4(pitch, roll, yaw):
    xc = math.cos(math.radians(pitch))
    xs = math.sin(math.radians(pitch))
    xm = [[1,0,0,0],
          [0,xc,-xs,0],
          [0,xs,xc,0],
          [0,0,0,1]]
    yc = math.cos(math.radians(roll))
    ys = math.sin(math.radians(roll))
    ym = [[yc,0,ys,0],
          [0,1,0,0],
          [-ys,0,yc,0],
          [0,0,0,1]]
    zc = math.cos(math.radians(yaw))
    zs = math.sin(math.radians(yaw))
    zm = [[zc,-zs,0,0],
          [zs,zc,0,0],
          [0,0,1,0],
          [0,0,0,1]]
    om = np.matmul(zm, ym)
    om = np.matmul(xm, om)
    return om

class CameraContext:
    def __init__(self,
                 position: list[float],
                 rotation: list[float],
                 fov: float,
                 surface: pygame.Surface):
        self.position = position
        self.rotation = rotation
        self.screen_size = (1,1)
        self.fov = fov
        self.frustum_width = 1
        self.frustum_height = 1
        self.surface = surface

    def update_screenspace(self):
        self.screen_size = (self.surface.get_width(), self.surface.get_height())

        self.min_render_distance = 0.1
        self.frustum_width = self.min_render_distance / (math.pi - math.radians(self.fov))
        self.frustum_height = self.frustum_width * (self.screen_size[1] / self.screen_size[0])
        #self.projection_matrix = [[nx/2,  0,     0,     (nx-1)/2],
        #                       [0,     ny/2,  0,     (ny-1)/2],
        #                       [0,     0,     1/2,   1/2     ]]

        f = 10 # far
        n = self.min_render_distance # near
        r = self.frustum_width # width
        t = self.frustum_height # height
        a = n/r
        b = n/t
        c = (-f-n)/(f-n)
        d = (-2*f*n)/(f-n)
        self.projection_matrix = [[a, 0, 0, 0],
                                  [0, b, 0, 0],
                                  [0, 0, c, d],
                                  [0, 0,-1, 0]]

        # From https://songho.ca/opengl/gl_transform.html

        self.translation_matrix = [[1, 0, 0, self.position[0]],
                                   [0, 1, 0, self.position[1]],
                                   [0, 0, 1, self.position[2]],
                                   [0, 0, 0, 1]]

        self.rotation_matrix = pry_rot_to_4x4(self.rotation[0], self.rotation[1], self.rotation[2])

        self.model_view_matrix = np.matmul(self.rotation_matrix, self.translation_matrix)
        self.combined_camera_matrix = np.matmul(self.projection_matrix, self.model_view_matrix)

    def transform_point(self, point):
        #point = transform_3d_point_4x4_mat(self.model_view_matrix, point)
        proj_point = transform_3d_point_4x4_mat(self.combined_camera_matrix, point)
        fsc = (proj_point[0], proj_point[1])
        ssc = ((fsc[0] + 0.5) * self.screen_size[0], (fsc[1] + 0.5) * self.screen_size[1])
        if proj_point[2] > 0: # Cull points behind camera
            return ssc
        else:
            return None

class Renderable():
    def __init__(self):
        pass

    def draw(self, camera_context: CameraContext):
        pass

class Object3d(Renderable):
    def __init__(self,
                 vertices: list[list[float]],
                 faces: list[list[int]],
                 color: Optional[list[int]] = None,
                 face_color: list[int] = None) -> None:
        self.__mod_vertices = [None] * len(vertices)
        #self.__mod_edges = edges
        #self.__mod_faces = faces
        self.vertices = vertices
        self.faces = faces
        self.face_color = face_color
        self.position = [0, 0, 0]
        self.color = color
        self.rotation_matrix = pry_rot_to_4x4(0, 0, 0)
        self.update_vertex_cache()
        edges = set()
        for face in self.faces:
            edges.add((face[0], face[1]))
            edges.add((face[1], face[2]))
            edges.add((face[2], face[0]))
        self.edges = list(edges)
        if self.color is None:
            if self.face_color is None:
                self.face_color = []
                for face in self.faces:
                    self.face_color.append([random.randint(0,255),random.randint(0,255),random.randint(0,255)])

                for face_idx in range(len(self.faces)):
                    print(str(self.faces[face_idx]) + " => " + str(self.face_color[face_idx]))

    def set_rotation(self, pitch, roll, yaw):
        self.rotation_matrix = pry_rot_to_4x4(pitch, roll, yaw)
        self.update_vertex_cache()

    def set_position(self, x, y, z):
        self.position = [x, y, z]
        self.update_vertex_cache()

    def update_vertex_cache(self):
        for vindex, vertex in enumerate(self.vertices):
            vertex = transform_3d_point_4x4_mat(self.rotation_matrix, vertex)
            self.__mod_vertices[vindex] = [vertex[0] + self.position[0], vertex[1] + self.position[1], vertex[2] + self.position[2]]

    def draw_wireframe(self, camera_context: CameraContext) -> None:
        scr_center = (camera_context.screen_size[0] / 2, camera_context.screen_size[1] / 2)
        tpf = camera_context.transform_point
        for edge in self.edges:
            p1 = tpf(self.__mod_vertices[edge[0]])
            p2 = tpf(self.__mod_vertices[edge[1]])
            if p1 is not None and p2 is not None:
                pygame.draw.line(camera_context.surface, self.color, p1, p2)

    def draw(self, camera_context: CameraContext) -> None:
        scr_center = (camera_context.screen_size[0] / 2, camera_context.screen_size[1] / 2)
        tpf = camera_context.transform_point
        for idx, face in enumerate(self.faces):
            poly_points = [tpf(self.__mod_vertices[face[0]]),
                    tpf(self.__mod_vertices[face[1]]),
                    tpf(self.__mod_vertices[face[2]])]

            dir_sum = 0
            for edgeidx in range(3):
                p1 = poly_points[edgeidx]
                p2 = poly_points[(edgeidx + 1) % 3]
                dir_sum += (p2[0] - p1[0]) * (p2[1] + p1[1])
            backface_cull = dir_sum < 0

            #if not backface_cull:
            if self.color is None:
                if backface_cull:
                    #pygame.draw.lines(camera_context.surface, self.face_color[idx], True, poly_points)
                    pass
                else:
                    pygame.draw.polygon(camera_context.surface, self.face_color[idx], poly_points)


                #for ptidx in range(3):
                #    text_surface = sans_font.render(str(face[ptidx]), False, (255,255,255))
                #    camera_context.surface.blit(text_surface, poly_points[ptidx])
            else:
                if not backface_cull:
                    pygame.draw.polygon(camera_context.surface, self.color, poly_points)


class Cube(Object3d):
    faces: list[list[int]] = [
        [0,1,2],
        [0,2,3],

        [4,7,6],
        [6,5,4],

        [5,2,1],
        [6,2,5],

        [5,1,4],
        [4,1,0],

        [7,0,3],
        [4,0,7],

        [7,3,6],
        [6,3,2]
    ]
    def __init__(self, size, color = None) -> None:
        size = size/2
        vertices: list[list[float]] = [
            [-size, -size, -size],
            [size, -size, -size],
            [size, size, -size],
            [-size, size, -size],
            [-size, -size, size],
            [size, -size, size],
            [size, size, size],
            [-size, size, size]
        ]
        super().__init__(vertices, Cube.faces, color)

class Ellipsoid(Object3d):
    def __init__(self, n_meridians, n_parallels, diameter, flattening, color = None) -> None:
        compression_factor = 1 - flattening
        radius = diameter/2
        vertices = [[0,0,radius * compression_factor],[0,0,-radius * compression_factor]]
        faces = []
        for ipa in range(n_parallels):
            vang = ((ipa + 1) / (n_parallels + 1)) * math.pi
            vpos = -math.cos(vang) * radius * compression_factor
            for ime in range(n_meridians):
                ang = (ime * math.pi * 2) / n_meridians
                sa = math.sin(ang)
                ca = math.cos(ang)
                slice_rad = math.sin(vang) * radius
                vertices.append([sa * slice_rad,ca * slice_rad,vpos])

        # bottom cap
        for ime in range(n_meridians):
            faces.append([2+ime,1,2+((ime+1)%n_meridians)])

        # top cap
        for ime in range(n_meridians):
            bc_offset = (n_meridians * (n_parallels - 1))
            faces.append([0,2+ime+bc_offset,2+((ime+1)%n_meridians)+bc_offset])

        # panels
        for ipa in range(n_parallels - 1):
            for ime in range(n_meridians):
                pt1 = 2+((ime + 0)%n_meridians)+(n_meridians * ipa)
                pt2 = 2+((ime + 0)%n_meridians)+(n_meridians * (ipa + 1))
                pt3 = 2+((ime + 1)%n_meridians)+(n_meridians * ipa)
                pt4 = 2+((ime + 1)%n_meridians)+(n_meridians * (ipa + 1))
                faces.append([pt2, pt1, pt3])
                faces.append([pt2, pt3, pt4])
                #edges.append([2+ime+(n_meridians * (ipa + 1)),2+ime+(n_meridians * ipa)])

        super().__init__(vertices, faces, color)

class Sphere(Ellipsoid):
    def __init__(self, n_meridians, n_parallels, diameter, color = None) -> None:
        super().__init__(n_meridians, n_parallels, diameter, 0, color)

class PointCloud(Renderable):
    def __init__(self, diameter = 2) -> None:
        self.diameter = diameter
        self.points = []
        self.__mod_points = []
        self.colors = []

    def add_point(self, point, color):
        self.points.append((point, len(self.colors)))
        self.__mod_points = self.points
        self.colors.append(color)

    def draw(self, camera_context: CameraContext) -> None:
        #pixel_array = pygame.PixelArray(camera_context.surface)

        scr_center = (camera_context.screen_size[0] / 2, camera_context.screen_size[1] / 2)

        for point in self.points:
            p1 = camera_context.transform_point(point[0])
            #pixel_array[p1[0], p1[1]] = self.colors[point[1]]
            pygame.draw.circle(camera_context.surface, self.colors[point[1]], p1, self.diameter/2)
        #pixel_array[start_x:end_x, start_y:end_y] = color

        #pixel_array.close()
