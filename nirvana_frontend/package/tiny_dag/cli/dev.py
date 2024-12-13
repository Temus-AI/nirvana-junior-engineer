import os
from honcho.manager import Manager
from pathlib import Path

def run_frontend():
    try:

        current_file = Path(__file__).resolve()
        print(f"Current file location: {current_file}")
        
        project_root = current_file.parents[4]
        print(f"Project root: {project_root}")
        
        frontend_dir = project_root / "nirvana_frontend" / "src"
        print(f"Frontend directory: {frontend_dir}")
        
        if not frontend_dir.exists():
            print(f"ERROR: Frontend directory does not exist: {frontend_dir}")
            return
        

        os.chdir(frontend_dir)
        print(f"Changed directory to: {os.getcwd()}")
        
        os.system('npm install && npm run dev -- --host 0.0.0.0')
    except Exception as e:
        print(f"Error in run_frontend: {str(e)}")

def run_dev():
    try:
        os.environ['PYTHONUNBUFFERED'] = '1'
        
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[4]
        frontend_dir = project_root / "nirvana_frontend" / "src"
        
        print(f"Starting manager with paths:")
        print(f"Project root: {project_root}")
        print(f"Frontend dir: {frontend_dir}")
        
        manager = Manager()
        
        frontend_cmd = f'cd {frontend_dir} && npm install && npm run dev -- --host 0.0.0.0'
        print(f"Frontend command: {frontend_cmd}")
        
        manager.add_process('frontend', frontend_cmd)
        manager.add_process('backend', 'tiny_dag_backend')
        
        manager.loop()
    except Exception as e:
        print(f"Error in run_dev: {str(e)}")

if __name__ == "__main__":
    run_dev()