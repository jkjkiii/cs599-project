import os

def get_project_root() -> str:
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
    return project_root

def get_abs_path(relative_path: str) -> str:
    # 获取项目根目录
    project_root = get_project_root()
    # 拼接项目根目录和相对路径，得到绝对路径
    abs_path = os.path.join(project_root, relative_path)
    return abs_path