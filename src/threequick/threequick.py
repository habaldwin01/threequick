import pygame
import pygame.font
import numpy as np
import math
import random
from typing import Optional, Union
import drawsvg as draw


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

class Object3d:
    def __init__(self,
                 vertices: list[list[float]],
                 faces: list[list[int]],
                 color: Optional[list[int]] = None,
                 face_color: Optional[list[int]] = None,
                 vertex_color: Optional[list[int]] = None,
                 filled: bool = True,
                 stroke_width: int = 0) -> None:
        self.__mod_vertices = [None] * len(vertices)
        #self.__mod_edges = edges
        #self.__mod_faces = faces
        self.vertices = vertices
        self.faces = faces
        self.face_color = face_color
        self.vertex_color = vertex_color
        self.position = [0, 0, 0]
        self.color = color
        self.rotation_matrix = pry_rot_to_4x4(0, 0, 0)
        self.update_vertex_cache()
        self.filled = filled
        self.stroke_width = stroke_width
        self.__avg_depth = 0
        self.fixed_depth = None
        edges = set()
        for face in self.faces:
            edges.add((face[0], face[1]))
            edges.add((face[1], face[2]))
            edges.add((face[2], face[0]))
        self.edges = list(edges)
        if self.color is None:
            if self.face_color is None:
                if self.vertex_color is None:
                    self.set_random_face_color()


                
    def set_random_face_color(self):
        self.face_color = []
        for face in self.faces:
            self.face_color.append([random.randint(0,255),random.randint(0,255),random.randint(0,255)])
            
    def set_random_vertex_color(self):
        self.vertex_color = []
        for vertex in self.vertices:
            self.vertex_color.append([random.randint(0,255),random.randint(0,255),random.randint(0,255)])

    def set_rotation(self, pitch, roll, yaw):
        self.rotation_matrix = pry_rot_to_4x4(pitch, roll, yaw)
        self.update_vertex_cache()

    def set_position(self, x, y, z):
        self.position = [x, y, z]
        self.update_vertex_cache()
        
    def get_modified_vertices(self):
        return self.__mod_vertices
    
    def get_faces(self):
        return self.faces

    def update_vertex_cache(self):
        for vindex, vertex in enumerate(self.vertices):
            vertex = transform_3d_point_4x4_mat(self.rotation_matrix, vertex)
            self.__mod_vertices[vindex] = [vertex[0] + self.position[0], vertex[1] + self.position[1], vertex[2] + self.position[2]]

    def apply_tpf(self, tpf):
        self.__transformed_tris = []

        for idx, face in enumerate(self.faces):
            poly_points = [tpf(self.__mod_vertices[face[0]]),
                    tpf(self.__mod_vertices[face[1]]),
                    tpf(self.__mod_vertices[face[2]])]

            dir_sum = 0
            for edgeidx in range(3):
                p1 = poly_points[edgeidx][0]
                p2 = poly_points[(edgeidx + 1) % 3][0]
                dir_sum += (p2[0] - p1[0]) * (p2[1] + p1[1])
            backface_cull = dir_sum < 0


            rt = None
            if self.color is None:
                if backface_cull:
                    pass
                else:
                    rt = (poly_points, (self.face_color[idx], self.face_color[idx], self.face_color[idx]))
            else:
                if not backface_cull:
                    rt = (poly_points, (self.color[idx], self.color[idx], self.color[idx]))

            if rt is not None:
                self.__transformed_tris.append(rt)

    def get_svg_components(self):
        poly_out = []
        for tri in self.__transformed_tris:
            tri_points = tri[0]
            tri_colors = tri[1]
            depth = min(tri_points[0][1], tri_points[1][1], tri_points[2][1])
            poly_out.append((draw.Lines(
                tri_points[0][0][0], tri_points[0][0][1],
                tri_points[1][0][0], tri_points[1][0][1],
                tri_points[2][0][0], tri_points[2][0][1],
                close=True,
                fill="#{:02X}{:02X}{:02X}".format(*tri_colors[0]),
                stroke='none'), depth))
        return poly_out

class Line3d:
    def __init__(self,
                 vertices: list[list[float]],
                 color: Optional[list[int]] = None,
                 vertex_color: Optional[list[int]] = None,
                 start_arrow: int = 0,
                 end_arrow: int = 0,
                 stroke_width: int = 1, 
                 screen_space_displace: list[int] = [0,0]) -> None:
        
        self.vertices = vertices
        self.color = color
        self.vertex_color = vertex_color
        self.end_arrow = end_arrow
        self.start_arrow = start_arrow
        self.stroke_width = stroke_width
        self.screen_space_displace = screen_space_displace
        self.fixed_depth = None
        
        if self.color is None:
            if self.vertex_color is None:
                self.set_random_vertex_color()
                    
    def set_random_vertex_color(self):
        self.vertex_color = []
        for vertex in self.vertices:
            self.vertex_color.append([random.randint(0,255),random.randint(0,255),random.randint(0,255)])

    def apply_tpf(self, tpf):
        self.__transformed_points = []
        for vertex in self.vertices:
            self.__transformed_points.append(tpf(vertex))

    def get_svg_components(self):
        poly_out = []
        if self.fixed_depth is None:
            depth = min(self.__transformed_points, key=lambda p: p[1])[1]
        else:
            depth = self.fixed_depth
        pts = []
        for point in self.__transformed_points:
            pts.append(point[0][0] + self.screen_space_displace[0])
            pts.append(point[0][1] + self.screen_space_displace[1])
        poly_out.append((draw.Lines(*pts,
                    close=False,
                    stroke="#{:02X}{:02X}{:02X}".format(*self.color),
                    stroke_width=self.stroke_width,
                    stroke_linecap='round',
                    fill='none'), depth))
        if self.end_arrow > 0:
            end_pt = [pts[-2], pts[-1]]
            end_vec = [pts[-2] - pts[-4], pts[-1] - pts[-3]]
            vec_len = math.sqrt((end_vec[0]**2) + (end_vec[1]**2))
            end_perp_vec = [end_vec[1]/vec_len/2, -end_vec[0]/vec_len/2]
            end_vec = [end_vec[0]/vec_len, end_vec[1]/vec_len]
            end_lhs = [end_pt[0] + ((end_perp_vec[0] - end_vec[0]) * self.end_arrow), end_pt[1] + ((end_perp_vec[1] - end_vec[1]) * self.end_arrow)]
            end_rhs = [end_pt[0] + (-(end_perp_vec[0] + end_vec[0]) * self.end_arrow), end_pt[1] + (-(end_perp_vec[1] + end_vec[1]) * self.end_arrow)]
            poly_out.append((draw.Lines(*end_pt, *end_rhs, *end_lhs,
                    close=True,
                    stroke="#{:02X}{:02X}{:02X}".format(*self.color),
                    stroke_width=self.stroke_width,
                    stroke_linecap='round',
                    fill='none'), depth))
        return poly_out


class Text3d:
    def __init__(self,
                 position: list[float],
                 text: str,
                 size: int = 24,
                 color: Optional[list[int]] = None,
                 outline_color: Optional[list[int]] = None) -> None:

        self.position = position
        self.text = text
        self.size = size
        self.color = color
        self.outline_color = outline_color
        self.fixed_depth = None

        if self.color is None:
            if self.outline_color is None:
                self.set_random_color()

    def set_random_color(self):
        self.color = [random.randint(0,255),random.randint(0,255),random.randint(0,255)]

    def apply_tpf(self, tpf):
        self.pos2d = tpf(self.position)
        if self.fixed_depth is None:
            self.__cam_dist = self.pos2d[1]
        else:
            self.__cam_dist = self.fixed_depth

    def get_svg_components(self):
        if self.outline_color is None:
            sc = "none"
        else:
            sc = "#{:02X}{:02X}{:02X}".format(*self.outline_color)
        if self.color is None:
            fc = "none"
        else:
            fc = "#{:02X}{:02X}{:02X}".format(*self.color)
        return [(draw.Text(self.text, font_size=self.size, x=self.pos2d[0][0], y=self.pos2d[0][1], stroke=sc, fill=fc, text_anchor="middle", dominant_baseline="middle", font_weight="bold"), self.__cam_dist)]

class CameraContext:
    def __init__(self,
                 position: list[float],
                 rotation: list[float],
                 fov: float,
                 screen_size: list[float]):
        self.position = position
        self.rotation = rotation
        self.screen_size = screen_size
        self.fov = fov
        self.frustum_width = 1
        self.frustum_height = 1
        self.surface = Surface(screen_size, self)
        
    def set_screen_size(self, width, height):
        self.screen_size = (width, height)
        self.surface.width = width
        self.surface.height = height

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
        ssc = ((proj_point[0]) * self.screen_size[0], (proj_point[1]) * self.screen_size[1])
        if proj_point[2] > 0: # Cull points behind camera
            return (ssc, proj_point[2])
        else:
            return None

class Surface:
    def __init__(self, canvas_size: list[int], camera_context: CameraContext):
        self.width = canvas_size[0]
        self.height = canvas_size[1]
        self.renderables = []
        self.camera_context = camera_context
    
    def get_width(self):
        return self.width    
    
    def get_height(self):
        return self.height
    
    def draw(self, obj: Union[Object3d, Line3d, Text3d]):
        obj.apply_tpf(self.camera_context.transform_point)
        self.renderables.append(obj)
    
    def to_drawsvg_obj(self):
        d = draw.Drawing(self.width, self.height, origin='center')

        components = []
        for renderable in self.renderables:
            components += renderable.get_svg_components()

        components.sort(key=lambda x: x[1], reverse=True)

        for component in components:
            d.append(component[0])
            
        return d
    
    def clear(self):
        del self.renderables
        self.renderables = []


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

