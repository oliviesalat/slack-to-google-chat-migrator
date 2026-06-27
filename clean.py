import os
import shutil

def clean_migration_files():
    removed = []

    for f in os.listdir('.'):
        if f.startswith('migration_') and f.endswith('.json'):
            os.remove(f)
            removed.append(f)

    if os.path.exists('media'):
        shutil.rmtree('media')
        removed.append('media/')

    if removed:
        print("Removed:")
        for r in removed:
            print(f"  {r}")
    else:
        print("Nothing to clean.")

if __name__ == "__main__":
    clean_migration_files()
