"""Vector-to-STL converter.

Converts closed 2D vector geometry into extruded STL meshes while preserving
source fidelity by rejecting invalid or open geometry.
"""

import sys
import os
import trimesh
import subprocess
from shapely.geometry import MultiPolygon


class UserFileError(ValueError):
    """Raised when uploaded vector geometry is invalid for conversion."""


def _convert_ps_to_dxf_if_needed(input_path):
    """Convert EPS/PDF input to a temporary DXF when needed."""
    if not input_path.lower().endswith((".eps", ".pdf")):
        return input_path, None

    ext = os.path.splitext(input_path)[1]
    print(f"[PYTHON VECTOR] {ext} detected. Converting to DXF...")

    temp_dxf = input_path + ".converted.dxf"
    cmd = ["pstoedit", "-dt", "-f", "dxf:-polyaslines", input_path, temp_dxf]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0 or not os.path.exists(temp_dxf):
        raise UserFileError("The uploaded file could not be read as valid vector geometry.")

    return temp_dxf, temp_dxf


def _load_path_layers(input_path):
    """Load 2D vector layers as Path2D objects."""
    try:
        loaded = trimesh.load(input_path, force='path')
    except Exception as exc:
        raise UserFileError("The uploaded vector file is not supported or is corrupted.") from exc

    if isinstance(loaded, trimesh.Scene):
        paths = [geom for geom in loaded.geometry.values() if isinstance(geom, trimesh.path.Path2D)]
    elif isinstance(loaded, trimesh.path.Path2D):
        paths = [loaded]
    else:
        paths = []

    if not paths:
        raise UserFileError("The uploaded file does not contain usable 2D vector shapes.")

    return paths


def _iter_valid_polygons(path):
    """Yield valid polygons from a Path2D object only."""
    try:
        polygons = list(path.polygons_full) or list(path.polygons_closed)
    except Exception as exc:
        raise UserFileError("The uploaded vector file could not be parsed into closed shapes.") from exc

    if not polygons:
        raise UserFileError("The vector file contains open curves/paths. Please close the shapes and upload again.")

    for polygon in polygons:
        candidates = polygon.geoms if isinstance(polygon, MultiPolygon) else [polygon]
        for candidate in candidates:
            if candidate.is_empty:
                continue
            if not candidate.is_valid:
                raise UserFileError("The vector file contains invalid shapes. Please fix the file and try again.")
            yield candidate


def _extrude_paths(paths, depth_mm):
    """Extrude all valid polygons from all path layers."""
    extruded_meshes = []
    for path in paths:
        for polygon in _iter_valid_polygons(path):
            try:
                mesh = trimesh.creation.extrude_polygon(polygon, height=depth_mm)
            except Exception as exc:
                raise UserFileError("The vector file could not be converted to a solid mesh.") from exc

            if not mesh.is_empty:
                extruded_meshes.append(mesh)

    if not extruded_meshes:
        raise UserFileError("No printable closed geometry was found in the uploaded vector file.")

    return trimesh.util.concatenate(extruded_meshes)


def _position_on_build_plate(mesh):
    """Center mesh and place it on Z=0 plane."""
    mesh.apply_translation(-mesh.centroid)
    min_z = mesh.bounds[0][2]
    mesh.apply_translation([0, 0, -min_z])


def vector_to_stl(input_path, output_path, depth_mm=2.0):
    """Convert vector geometry to STL by linear extrusion.

    Args:
        input_path: Path to input vector file (.dxf, .svg, .eps, .pdf).
        output_path: Destination STL output path.
        depth_mm: Extrusion depth in millimeters.

    Returns:
        None. Writes STL output to disk.

    Raises:
        SystemExit: If input geometry is invalid or conversion fails.
    """
    print(f"[PYTHON VECTOR] Processing: {input_path}")
    
    temp_dxf = None

    try:
        processing_path, temp_dxf = _convert_ps_to_dxf_if_needed(input_path)
        geometries = _load_path_layers(processing_path)

        print(f"[PYTHON VECTOR] Found {len(geometries)} geometry layers. Processing...")
        combined_mesh = _extrude_paths(geometries, depth_mm)
        _position_on_build_plate(combined_mesh)

        combined_mesh.export(output_path)
        print(f"[PYTHON VECTOR] Success! Exported to {output_path}")

    except UserFileError as e:
        print(f"[PYTHON VECTOR] ERROR: {e}")
        sys.exit(1)
    except Exception:
        print("[PYTHON VECTOR] ERROR: Failed to convert this vector file.")
        sys.exit(1)
        
    finally:
        if temp_dxf and os.path.exists(temp_dxf):
            try:
                os.remove(temp_dxf)
            except OSError:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 vector2stl.py input.(dxf|svg|eps|pdf) output.stl")
        sys.exit(1)
    
    depth = 2.0
    if len(sys.argv) > 3:
        try:
            depth = float(sys.argv[3])
        except ValueError:
            pass
            
    vector_to_stl(sys.argv[1], sys.argv[2], depth)