"""
Packages the TrustLens project into a clean deployable ZIP archive.
Excludes node_modules, .git, .env (secrets), __pycache__, dist, and cache files.
"""
import os
import zipfile
import sys

EXCLUDE_DIRS = {
    'node_modules',
    '.git',
    '.pytest_cache',
    '__pycache__',
    'dist',
    '.system_generated',
}

EXCLUDE_FILES = {
    '.env',
    'trustlens_deployment.zip',
}

def package_project(output_zip: str = 'trustlens_deployment.zip'):
    root_dir = os.path.abspath('.')
    print(f"Creating clean archive: {output_zip}...")
    file_count = 0
    total_bytes = 0

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(root_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.endswith('.egg-info')]

            for file in files:
                if file in EXCLUDE_FILES or file.endswith('.pyc') or file.endswith('.log'):
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)

                zf.write(file_path, rel_path)
                file_count += 1
                total_bytes += os.path.getsize(file_path)

    zip_size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"Packaged {file_count} files ({total_bytes / (1024 * 1024):.1f} MB uncompressed) into {output_zip} ({zip_size_mb:.1f} MB compressed).")
    return output_zip

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'trustlens_deployment.zip'
    package_project(out)
