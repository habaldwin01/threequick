import math
from .renderer import Object3d

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
