# Sphere Gear — Spherical Gear Generator

Generates two mating gears:

- **Spherical Gear** — a sphere-shaped gear (intersection of two revolved involute profiles)
- **Monopole Gear** — a cylindrical gear whose teeth are cut by rolling the spherical gear around it

Both gears mesh together with the correct conjugate tooth profile. The Spherical Gear is automatically split into two halves for easy 3D printing, with integrated alignment pins and screw holes for assembly.

## How It Works

### Spherical Gear (`spherical_gear.py`)

1. `py_gearworks` builds a precise involute tooth profile (Wire in the XY plane)
2. The profile is split in half twice — along X and along Y — producing two half-contours
3. Each half-contour is revolved around its respective axis — producing two solids of revolution
4. Boolean intersection (`^`) via `manifold3d` yields a sphere with teeth along both axes
5. The sphere is cut in half at Z=0 for 3D printing.
6. Alignment pin holes and counterbored screw holes are subtracted from the flat face.

### Rectangular Pin (`rect_pin.py`)

Generates a single rectangular alignment pin (`rect_pin.stl`) used to precisely align and connect the two halves of the spherical gear.
- Features integrated holes/clearances for assembly.
- Automatically scales its length and thickness based on the sphere's diameter.
- Features chamfers and fillets for easy insertion.

### Monopole Gear (`monopole_gear.py`)

1. A cylindrical blank is created (with a bore hole and chamfers)
2. A 3D cutter is built — the tooth profile revolved around the X axis (simulating the spherical gear)
3. The cutter rolls around the blank in 720 steps:
   - At each step the cutter spins around its own axis and orbits around the blank
   - Gear ratio: spin/orbit = `MONOPOLE_TEETH / TEETH`
4. The result is a cylinder with curved teeth perfectly conjugate to the spherical gear

### Configuration (`config.py`)

All parameters in one place: diameter, tooth count, angles, and assembly toggles.

## Installation

Python **3.10+** (tested on 3.13).

```bash
pip install -r requirements.txt
```

Alternatively, install the required packages individually:

```bash
pip install build123d numpy trimesh manifold3d py-gearworks
```

| Package | Purpose |
|---|---|
| `build123d` | Parametric 3D modeling (OpenCascade wrapper) |
| `py-gearworks` | Precise involute tooth profile generation |
| `manifold3d` | Fast boolean mesh operations (replaces slow OCCT booleans) |
| `trimesh` | Triangle mesh processing and STL export |
| `numpy` | Numeric arrays for mesh data |

> **Note:** `build123d` pulls in OpenCascade (~300 MB), the first install may take a while.

## Usage

```bash
# Generate the spherical gear half
python spherical_gear.py

# Generate the alignment pin
python rect_pin.py

# Generate the monopole gear (takes several minutes)
python monopole_gear.py
```

Output files (`spherical_gear.stl`, `rect_pin.stl`, `monopole_gear.stl`) will be saved in the current directory.

## Assembly & Hardware

To assemble the Spherical Gear, you will need to print **2x `spherical_gear.stl`** and **4x `rect_pin.stl`**.

Recommended hardware (for default settings):
- **4x M3 Heat-Set Inserts** (4.5mm OD, 5mm Length) - melt these into the top and bottom of the printed hex pins.
- **4x M3 Socket Head Screws (DIN 912)** - The default `SCREW_CLAMP_THICKNESS` requires an **M3x16** screw to perfectly clamp the halves together without bottoming out.

The screws are inserted from the outside of the sphere halves. The counterbore ensures the screw heads sit deep inside the gear valleys and will not interfere with the gear rotation.

## Modular Configuration

All parameters are set in `config.py`. The assembly features can be toggled on/off:

```python
# ==========================================
# ASSEMBLY OPTIONS
# ==========================================
ENABLE_PINS = True                # Generate hex pin holes?
ENABLE_SCREWS = True              # Generate through-holes for clamping screws?
ENABLE_THREADED_INSERTS = True    # Generate holes for heat-set inserts in pins?

# Basic Parameters
DIAMETER = 100.0          # Outer sphere diameter (mm)
TEETH = 32               # Spherical gear tooth count
```

All pin dimensions, offsets, and hole depths are mathematically calculated to automatically scale with your `DIAMETER` and `TEETH` settings while maintaining safe 3D printing tolerances.
