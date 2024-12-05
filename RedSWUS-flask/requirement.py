import sys
import os
import subprocess
import distutils.core

def install_pyyaml():
    print("Installing PyYAML...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml==5.1"])

def clone_detectron2_repo():
    print("Cloning Detectron2 repository...")
    if not os.path.exists("detectron2"):
        subprocess.check_call(["git", "clone", "https://github.com/facebookresearch/detectron2"])
    else:
        print("Detectron2 repository already exists. Skipping clone.")

def install_detectron2_dependencies():
    print("Installing Detectron2 dependencies...")
    dist = distutils.core.run_setup("./detectron2/setup.py")
    # Clean up dependencies to remove extra quotes
    dependencies = [x.strip("'\"") for x in dist.install_requires]
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *dependencies])
        print("Detectron2 dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Detectron2 dependencies: {e}")

def add_detectron2_to_path():
    print("Adding Detectron2 to Python path...")
    sys.path.insert(0, os.path.abspath('./detectron2'))

def main():
    install_pyyaml()
    clone_detectron2_repo()  # Change directory to detectron2
    install_detectron2_dependencies()
    os.chdir("..")  # Return to the previous directory
    add_detectron2_to_path()
    print("Detectron2 installed and ready to use.")

if __name__ == "__main__":
    main()
