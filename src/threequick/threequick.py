import pygame
import numpy as np
import math

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
        self.frustum_width = self.min_render_distance * math.radians(self.fov)
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
                 edges: list[list[int]],
                 faces: list[list[int]]) -> None:
        self.__mod_vertices = [None] * len(vertices)
        #self.__mod_edges = edges
        #self.__mod_faces = faces
        self.vertices = vertices
        self.edges = edges
        self.faces = faces
        self.position = [0, 0, 0]
        self.rotation_matrix = pry_rot_to_4x4(0, 0, 0)
        self.update_vertex_cache()

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

    def draw(self, camera_context: CameraContext) -> None:
        scr_center = (camera_context.screen_size[0] / 2, camera_context.screen_size[1] / 2)
        tpf = camera_context.transform_point
        for edge in self.edges:
            p1 = tpf(self.__mod_vertices[edge[0]])
            p2 = tpf(self.__mod_vertices[edge[1]])
            if p1 is not None and p2 is not None:
                pygame.draw.line(camera_context.surface, (255, 255, 255), p1, p2)

class Cube(Object3d):
    edges: list[list[int]] = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
        [4, 5],
        [5, 6],
        [6, 7],
        [7, 4],
        [0, 4],
        [1, 5],
        [2, 6],
        [3, 7]
    ]
    faces: list[list[int]] = [
        [0, 1, 2],
        [1, 2, 3],
        [4, 5, 6],
        [5, 6, 7],
        [0, 1, 5],
        [1, 5, 4],
        [1, 2, 6],
        [2, 6, 5],
        [2, 3, 7],
        [3, 7, 6],
        [3, 0, 4],
        [0, 4, 7]
    ]
    def __init__(self, size) -> None:
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
        super().__init__(vertices, Cube.edges, Cube.faces)

class Sphere(Object3d):
    def __init__(self, n_meridians, n_parallels, diameter) -> None:
        radius = diameter/2
        vertices = [[0,0,radius],[0,0,-radius]]
        edges = []
        faces = []
        for ipa in range(n_parallels):
            vang = ((ipa + 1) / (n_parallels + 1)) * math.pi
            vpos = -math.cos(vang) * radius
            for ime in range(n_meridians):
                ang = (ime * math.pi * 2) / n_meridians
                sa = math.sin(ang)
                ca = math.cos(ang)
                slice_rad = math.sin(vang) * radius
                vertices.append([sa * slice_rad,ca * slice_rad,vpos])

        # bottom cap
        for ime in range(n_meridians):
            edges.append([1,2+ime])

        # top cap
        for ime in range(n_meridians):
            edges.append([0,2+ime+(n_meridians * (n_parallels - 1))])

        # meridians
        for ipa in range(n_parallels - 1):
            for ime in range(n_meridians):
                edges.append([2+ime+(n_meridians * (ipa + 1)),2+ime+(n_meridians * ipa)])

        # parallels
        for ipa in range(n_parallels):
            for ime in range(n_meridians):
                edges.append([2+ime+(n_meridians * ipa),2+((ime + 1)%n_meridians)+(n_meridians * ipa)])

        super().__init__(vertices, edges, faces)


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
