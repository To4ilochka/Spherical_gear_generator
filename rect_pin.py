from build123d import *
import config
import math
import trimesh
from utils import shape_to_manifold
import os

print("==========================================")
print(" GENERATING SINGLE RECTANGULAR PIN")
print("==========================================")

with BuildPart() as pin:
    with BuildSketch(Plane.XY):
        Rectangle(width=config.PIN_DIAMETER, height=config.PIN_DIAMETER)
    extrude(amount=config.PIN_LENGTH)
    
    top_faces = pin.faces().filter_by(Axis.Z)
    bottom_faces = pin.faces().filter_by(Axis.Z, reverse=True)
    
    end_edges = []
    for face in top_faces:
        end_edges.extend(face.outer_wire().edges())
    for face in bottom_faces:
        end_edges.extend(face.outer_wire().edges())
    try:
        chamfer(end_edges, length=0.6)
    except:
        pass
    
    vertical_edges = pin.edges().filter_by(Axis.Z)
    try:
        fillet(vertical_edges, radius=0.5)
    except:
        pass

print("Tessellating to Manifold3D...")
m_pin = shape_to_manifold(pin.part)

print("Exporting results...")
out_mesh = m_pin.to_mesh()
result_mesh = trimesh.Trimesh(vertices=out_mesh.vert_properties[:, :3], faces=out_mesh.tri_verts)
result_mesh.export(config.OUTPUT_PIN_STL)
print(f"Success! Saved as {config.OUTPUT_PIN_STL}")
