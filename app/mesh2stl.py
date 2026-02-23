"""Mesh-to-STL conversion utility.

Loads supported polygonal mesh formats and exports normalized STL output.
"""

import sys
import trimesh


def _load_as_mesh(input_path):
    """Load input file and normalize to a single mesh."""
    mesh = trimesh.load(input_path)
    if isinstance(mesh, trimesh.Scene):
        print("[PYTHON] Input is a Scene, merging geometries...")
        if not mesh.geometry:
            raise ValueError("The uploaded file does not contain mesh geometry.")
        mesh = trimesh.util.concatenate(mesh.dump())
    return mesh

def convert_mesh_to_stl(input_path, output_path):
    """Convert a mesh or mesh scene to STL.

    Args:
        input_path: Path to input mesh (.obj, .3mf, etc.).
        output_path: Destination STL output path.

    Returns:
        None. Writes STL output to disk.

    Raises:
        SystemExit: If mesh loading or export fails.
    """
    print(f"[PYTHON] Loading mesh: {input_path}")
    try:
        mesh = _load_as_mesh(input_path)

        # 3. Exporting to STL
        mesh.export(output_path)
        print(f"[PYTHON] Success! Exported to {output_path}")

    except FileNotFoundError:
        print("[PYTHON] ERROR: Input mesh file was not found.")
        sys.exit(1)
    except ValueError as e:
        print(f"[PYTHON] ERROR: Invalid mesh file. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[PYTHON] ERROR: Could not convert this mesh file. {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 mesh2stl.py input.(obj|3mf) output.stl")
        sys.exit(1)

    convert_mesh_to_stl(sys.argv[1], sys.argv[2])