"""CAD-to-STL conversion utility.

Converts supported CAD interchange formats into STL meshes without applying
automatic geometry healing or shape correction to preserve source fidelity.
"""

import sys
import os
import shutil
import gmsh


class UserFileError(ValueError):
    """Raised when the uploaded CAD file is invalid."""


def _check_not_html(path):
    """Reject files that are actually downloaded HTML pages."""
    with open(path, 'rb') as file_obj:
        header = file_obj.read(256)

    try:
        text_header = header.decode('ascii', errors='ignore').lower()
    except Exception:
        return

    if "<!doctype html" in text_header or "<html" in text_header:
        raise UserFileError(
            "The uploaded file is not a valid CAD file. Please upload the original CAD export file."
        )

def convert_cad_to_stl(input_path, output_path):
    """Convert a CAD file to STL format.

    Args:
        input_path: Path to the source CAD file (.iges, .igs, .step, .stp).
        output_path: Destination STL output path.

    Returns:
        None. Writes STL output to disk.

    Raises:
        SystemExit: If conversion fails or source file is invalid.
    """
    input_abs_path = os.path.abspath(input_path)
    output_abs_path = os.path.abspath(output_path)
    
    print(f"[PYTHON CAD] Processing: {input_abs_path}")

    if not os.path.exists(input_abs_path):
        print("[PYTHON CAD] ERROR: Input CAD file was not found.")
        sys.exit(1)

    # 1. HTML check
    try:
        _check_not_html(input_abs_path)
    except UserFileError as e:
        print(f"[PYTHON CAD] ERROR: {e}")
        sys.exit(1)

    # 2. File extension handling
    temp_igs_path = input_abs_path
    created_temp_copy = False
    if input_abs_path.lower().endswith('.iges'):
        temp_igs_path = os.path.splitext(input_abs_path)[0] + '.igs'
        shutil.copy2(input_abs_path, temp_igs_path)
        created_temp_copy = True

    try:
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("General.Verbosity", 2)

        # 3. Loading and merging
        print("[PYTHON CAD] Merging file...")
        gmsh.merge(temp_igs_path)

        # 4. Synchronize imported geometry
        gmsh.model.occ.synchronize()

        # 5. Exporting to STL
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.5)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 5.0)

        gmsh.model.mesh.generate(2)
        
        # 6. Save
        gmsh.write(output_abs_path)
        print(f"[PYTHON CAD] Success! Exported to {output_abs_path}")

    except UserFileError as e:
        print(f"[PYTHON CAD] ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[PYTHON CAD] ERROR: Could not convert this CAD file. {str(e)}")
        sys.exit(1)
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()
        if created_temp_copy and os.path.exists(temp_igs_path):
            try:
                os.remove(temp_igs_path)
            except OSError:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 cad2stl.py input.(iges|igs|step|stp) output.stl")
        sys.exit(1)
        
    convert_cad_to_stl(sys.argv[1], sys.argv[2])