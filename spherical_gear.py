import py_gearworks as pgw
from build123d import *
import math
import config
import trimesh
from utils import shape_to_manifold

# Вычисляем модуль (module) автоматически, чтобы внешний диаметр совпадал с заданным.
# Внешний диаметр = module * (teeth + 2 * addendum_coefficient)
calc_module = config.DIAMETER / (config.TEETH + 2 * config.ADDENDUM_COEF)

# 1. Создаем профиль шестерни
gear = pgw.SpurGear(
    number_of_teeth=config.TEETH, 
    module=calc_module, 
    height=1,
    pressure_angle=math.radians(config.PRESSURE_ANGLE_DEG),
    backlash=config.BACKLASH,
    addendum_coefficient=config.ADDENDUM_COEF,
    dedendum_coefficient=config.DEDENDUM_COEF
)

# Получаем замкнутый Wire (контур зубьев) в плоскости XY
gear_wire = gear.build_boundary_wire(z_ratio=0)

if getattr(config, 'INVERT_PROFILE', False):
    gear_wire = gear_wire.rotate(Axis.Z, 180.0 / config.TEETH)

# Превращаем Wire в Sketch (заливаем в грань)
with BuildSketch() as fig1:
    with BuildLine():
        add(gear_wire)
    make_face()

# Вычисляем максимальный радиус шестерни для правильной обрезки с запасом
cut_size = config.DIAMETER * 1.5

# ==========================================
# 2. Отрезаем от фигуры1 половину по оси X (Контур 1, оставляем Y >= 0)
with BuildSketch() as contour1:
    add(fig1.sketch)
    with BuildSketch(mode=Mode.INTERSECT):
        Rectangle(cut_size, cut_size, align=(Align.CENTER, Align.MIN))

# 3. Отрезаем от фигуры1 половину по оси Y (Контур 2, оставляем X >= 0)
with BuildSketch() as contour2:
    add(fig1.sketch)
    with BuildSketch(mode=Mode.INTERSECT):
        Rectangle(cut_size, cut_size, align=(Align.MIN, Align.CENTER))

# ==========================================
# 4. Делаем тело вращения из контура1 по оси X (Тело 1)
with BuildPart() as b1:
    with BuildSketch(Plane.XY):
        add(contour1.sketch)
    revolve(axis=Axis.X)
body1 = b1.part

# 5. Делаем тело вращения из контура2 по оси Y (Тело 2)
with BuildPart() as b2:
    with BuildSketch(Plane.XY):
        add(contour2.sketch)
    revolve(axis=Axis.Y)
body2 = b2.part

# ==========================================
# 6. Получаем пересечение ДВУХ тел
print("Tessellating bodies for Manifold3D...")

# shape_to_manifold imported from utils.py

print("Converting to Manifold...")
m1 = shape_to_manifold(body1)
m2 = shape_to_manifold(body2)
m_res = m1 ^ m2

print("Cutting gear in half (Z >= 0) for 3D printing...")
with BuildPart() as b_half:
    Box(cut_size * 2, cut_size * 2, cut_size * 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
m_half = shape_to_manifold(b_half.part)
m_res = m_res ^ m_half

if getattr(config, 'ENABLE_PINS', True):
    print("Adding hexagonal pin holes...")
    with BuildPart() as b_holes:
        with BuildSketch(Plane.XY):
            with Locations((config.PIN_OFFSET, config.PIN_OFFSET),
                           (config.PIN_OFFSET, -config.PIN_OFFSET),
                           (-config.PIN_OFFSET, config.PIN_OFFSET),
                           (-config.PIN_OFFSET, -config.PIN_OFFSET)):
                Rectangle(width=config.PIN_DIAMETER + 2*config.PIN_TOLERANCE, height=config.PIN_DIAMETER + 2*config.PIN_TOLERANCE)
        extrude(amount=config.PIN_HOLE_DEPTH)
    m_holes = shape_to_manifold(b_holes.part)
    m_res = m_res - m_holes

if getattr(config, 'ENABLE_SCREWS', True):
    print("Adding screw clearance holes and counterbores...")
    with BuildPart() as b_screws:
        # Сквозное отверстие для винта (начинается чуть выше, оставляя сплошной "жертвенный слой" (sacrificial bridge)
        # чтобы принтер мог перекинуть мост над шестигранным отверстием без провисания в воздухе)
        with BuildSketch(Plane.XY.offset(config.PIN_HOLE_DEPTH + config.SACRIFICIAL_BRIDGE_THICKNESS)):
            with Locations((config.PIN_OFFSET, config.PIN_OFFSET),
                           (config.PIN_OFFSET, -config.PIN_OFFSET),
                           (-config.PIN_OFFSET, config.PIN_OFFSET),
                           (-config.PIN_OFFSET, -config.PIN_OFFSET)):
                Circle(radius=config.SCREW_CLEARANCE_HOLE / 2)
        extrude(amount=config.DIAMETER)

        # Углубление под шляпку винта
        with BuildSketch(Plane.XY.offset(config.PIN_HOLE_DEPTH + config.SCREW_CLAMP_THICKNESS)):
            with Locations((config.PIN_OFFSET, config.PIN_OFFSET),
                           (config.PIN_OFFSET, -config.PIN_OFFSET),
                           (-config.PIN_OFFSET, config.PIN_OFFSET),
                           (-config.PIN_OFFSET, -config.PIN_OFFSET)):
                Circle(radius=config.SCREW_HEAD_DIAMETER / 2)
        extrude(amount=config.DIAMETER)
    m_screws = shape_to_manifold(b_screws.part)
    m_res = m_res - m_screws

print("Exporting results...")
out_mesh = m_res.to_mesh()
result_mesh = trimesh.Trimesh(vertices=out_mesh.vert_properties[:, :3], faces=out_mesh.tri_verts)
result_mesh.export(config.OUTPUT_SPHERE_STL)
print(f"Success! Saved as {config.OUTPUT_SPHERE_STL} (STEP export skipped because Manifold3D works with meshes)")
