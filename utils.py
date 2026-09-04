import numpy as np
import trimesh
import manifold3d
import config

def shape_to_manifold(shape, tol=None, ang_tol=None):
    tol = tol or getattr(config, 'MESH_TOLERANCE', 0.01)
    ang_tol = ang_tol or getattr(config, 'MESH_ANGULAR_TOLERANCE', 0.1)
    
    v, t = shape.tessellate(tol, ang_tol)
    v_np = np.array([[vert.X, vert.Y, vert.Z] for vert in v], dtype=np.float32)
    t_np = np.array(t, dtype=np.uint32)
    mesh = trimesh.Trimesh(vertices=v_np, faces=t_np, process=True)
    mesh.fix_normals()
    return manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.array(mesh.vertices, dtype=np.float32),
        tri_verts=np.array(mesh.faces, dtype=np.uint32)
    ))
