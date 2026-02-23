"""Image-to-STL converter.

Builds a grayscale heightmap mesh from raster images and exports STL output
for slicing workflows.
"""

import sys
import numpy as np
from PIL import Image, UnidentifiedImageError
import trimesh


def _build_grid_faces(height, width):
    """Build triangle faces for a regular heightmap grid."""
    r = np.arange(height - 1)[:, None]
    c = np.arange(width - 1)[None, :]

    tl = (r * width + c).ravel()
    tr = (r * width + c + 1).ravel()
    bl = ((r + 1) * width + c).ravel()
    br = ((r + 1) * width + c + 1).ravel()

    first = np.column_stack((bl, tr, tl))
    second = np.column_stack((bl, br, tr))
    return np.vstack((first, second))

def image_to_stl(input_path, output_path, depth_mm=3.0, base_mm=0.5):
    """Convert a raster image to an STL heightmap mesh.

    Args:
        input_path: Path to input image (.jpg, .jpeg, .png, .bmp).
        output_path: Destination STL output path.
        depth_mm: Maximum emboss depth applied from pixel intensity.
        base_mm: Minimum base thickness for the generated mesh.

    Returns:
        None. Writes STL output to disk.

    Raises:
        SystemExit: If conversion fails.
    """
    print(f"[PYTHON IMG] Processing image: {input_path}")
    
    try:
        # 1. Load Image and Convert to Grayscale
        with Image.open(input_path) as raw_img:
            img = raw_img.convert('L')

        # 2. Resize if too large
        max_dim = 300
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim))
            print(f"[PYTHON IMG] Resized image to {img.width}x{img.height} for performance.")
        
        # 3. Process Pixel Data
        img_array = np.array(img)
        height, width = img_array.shape

        target_width_mm = 100.0
        pixel_size_mm = target_width_mm / width
        
        print(f"[PYTHON IMG] Physical dimensions will be approx: {target_width_mm:.2f}mm width.")

        # 4. Generate Vertex Grid
        x = np.arange(0, width) * pixel_size_mm
        y = np.arange(0, height) * pixel_size_mm
        X, Y = np.meshgrid(x, y[::-1])

        z_data = (255 - img_array) / 255.0 
        Z = base_mm + (z_data * depth_mm)
        
        vertices = np.column_stack((X.flatten(), Y.flatten(), Z.flatten()))
        
        # 5. Generate Faces
        faces = _build_grid_faces(height, width)
        
        # 6. Create Mesh using Trimesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # 7. Post-Processing
        mesh.fix_normals()
        
        mesh.apply_translation(-mesh.centroid)
        min_z = mesh.bounds[0][2]
        mesh.apply_translation([0, 0, -min_z])

        # 8. Export
        print(f"[PYTHON IMG] Saving STL to {output_path}")
        mesh.export(output_path)
        print("[PYTHON IMG] Success.")

    except FileNotFoundError:
        print("[PYTHON IMG] ERROR: Input image file was not found.")
        sys.exit(1)
    except UnidentifiedImageError:
        print("[PYTHON IMG] ERROR: Invalid image file. Please upload a supported image format.")
        sys.exit(1)
    except ValueError as e:
        print(f"[PYTHON IMG] ERROR: Invalid image content. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[PYTHON IMG] ERROR: Could not convert this image file. {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 img2stl.py input.(jpg|jpeg|png|bmp) output.stl")
        sys.exit(1)
        
    depth = 3.0
    if len(sys.argv) > 3:
        try:
            depth = float(sys.argv[3])
        except ValueError:
            pass
            
    image_to_stl(sys.argv[1], sys.argv[2], depth)