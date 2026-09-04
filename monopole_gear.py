from build123d import *
import math
import numpy as np
import manifold3d
import trimesh
import time
import sys
import config
import py_gearworks as pgw
from utils import shape_to_manifold

print("==========================================")
print(" 1. CALCULATE PARAMETERS")
print("==========================================")
calc_module = config.DIAMETER / (config.TEETH + 2 * config.ADDENDUM_COEF)
print(f"Module: {calc_module:.4f}")

r_sph = (config.TEETH * calc_module) / 2.0
r_mono = (config.MONOPOLE_TEETH * calc_module) / 2.0
print(f"Spherical gear pitch radius: {r_sph:.2f} mm")
print(f"Monopole gear pitch radius: {r_mono:.2f} mm")

path_radius = r_sph + r_mono
print(f"Distance between centers: {path_radius:.2f} mm")

num_steps = 720  # Ultra-high res (requires intermediate baking)
orbit_step = 360.0 / num_steps
spin_ratio = config.MONOPOLE_TEETH / config.TEETH
spin_step = orbit_step * spin_ratio

print("\n==========================================")
print(" 2. CREATE BASE PART")
print("==========================================")
blank_radius = r_mono + (calc_module * config.ADDENDUM_COEF) + 0.5
# Высота заготовки: полная высота зуба каттера * 2 + запас
tooth_height = calc_module * (config.ADDENDUM_COEF + config.DEDENDUM_COEF)
blank_height = tooth_height * 2 + calc_module * 2

with BuildPart() as base_part:
    Cylinder(radius=blank_radius, height=blank_height)
    if config.MONOPOLE_BORE_DIAMETER > 0:
        Cylinder(radius=config.MONOPOLE_BORE_DIAMETER / 2.0, height=blank_height + 2, mode=Mode.SUBTRACT)
    
    # Chamfer outer edges
    outer_edges = base_part.edges().filter_by(GeomType.CIRCLE).sort_by(SortBy.RADIUS)[-2:]
    chamfer_size = min(1.0, calc_module * 0.5)
    chamfer(outer_edges, length=chamfer_size)

print("\n==========================================")
print(" 3. CREATE 3D CUTTER (TRUE INVOLUTE)")
print("==========================================")
gear = pgw.SpurGear(
    number_of_teeth=config.TEETH, 
    module=calc_module, 
    height=1,
    pressure_angle=math.radians(config.PRESSURE_ANGLE_DEG),
    backlash=config.BACKLASH,
    addendum_coefficient=config.DEDENDUM_COEF,
    dedendum_coefficient=config.ADDENDUM_COEF
)
gear_wire = gear.build_boundary_wire(z_ratio=0)

if getattr(config, 'INVERT_PROFILE', False):
    gear_wire = gear_wire.rotate(Axis.Z, 180.0 / config.TEETH)

with BuildSketch() as fig1:
    with BuildLine():
        add(gear_wire)
    make_face()

cut_size = config.DIAMETER * 1.5
with BuildSketch() as half_gear:
    add(fig1.sketch)
    with BuildSketch(mode=Mode.INTERSECT):
        Rectangle(cut_size, cut_size, align=(Align.CENTER, Align.MIN))

with BuildPart() as cutter_part:
    add(half_gear)
    revolve(axis=Axis.X)

print("\n==========================================")
print(" 4. TESSELLATE TO MANIFOLD3D")
print("==========================================")
# shape_to_manifold imported from utils.py

t0 = time.time()
print("Tessellating base...")
m_base = shape_to_manifold(base_part.part, tol=0.01, ang_tol=0.1)
print("Tessellating cutter...")
m_cutter = shape_to_manifold(cutter_part.part, tol=0.01, ang_tol=0.1)
print(f"Tessellation done in {time.time()-t0:.2f}s")

print("\n==========================================")
print(f" 5. BOOLEAN SUBTRACTION ({num_steps} steps)")
print("==========================================")
t0 = time.time()
for i in range(num_steps):
    if i % 100 == 0:
        print(f"Progress: {i}/{num_steps}")
        sys.stdout.flush()
        
    orbit_angle = i * orbit_step
    spin_angle = i * spin_step
    
    m_cutter_inst = m_cutter.rotate([0, 0, spin_angle])
    m_cutter_inst = m_cutter_inst.translate([path_radius, 0, 0])
    m_cutter_inst = m_cutter_inst.rotate([0, 0, orbit_angle])
    
    m_base = m_base - m_cutter_inst
    
    # Bake the CSG tree periodically to avoid Out-Of-Memory errors
    if i % 180 == 0 and i > 0:
        print("Baking intermediate CSG tree to memory...")
        sys.stdout.flush()
        out_mesh = m_base.to_mesh()
        m_base = manifold3d.Manifold(manifold3d.Mesh(
            vert_properties=np.array(out_mesh.vert_properties, dtype=np.float32),
            tri_verts=np.array(out_mesh.tri_verts, dtype=np.uint32)
        ))
        
print(f"Boolean CSG tree built in {time.time()-t0:.2f}s")

print("\n==========================================")
print(" 6. EXPORTING FINAL MESH")
print("==========================================")
print("Evaluating CSG tree (this may take several minutes)...")
sys.stdout.flush()
t0 = time.time()

out_mesh = m_base.to_mesh()

print(f"Evaluation completed in {time.time()-t0:.2f}s")
result_mesh = trimesh.Trimesh(vertices=out_mesh.vert_properties[:, :3], faces=out_mesh.tri_verts)
result_mesh.export(config.OUTPUT_MONOPOLE_STL)
print(f"\nDone! Saved as {config.OUTPUT_MONOPOLE_STL}")
