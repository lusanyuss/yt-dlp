import os


class DirectoryManager:
    def __init__(self):
        self.base_path = os.getcwd()
        self.utils = os.path.join(self.base_path, "01_utils")
        self.source_directory = os.path.join(self.base_path, "02_source_directory")
        self.working_directory = os.path.join(self.base_path, "03_working_directory")
        self.output_directory = os.path.join(self.base_path, "04_output_directory")
        self.history_directory = os.path.join(self.base_path, "05_history_directory")
        self.assets = os.path.join(self.base_path, "06_assests")

    def get_directory(self, directory_name):
        return getattr(self, directory_name, None)

    def list_files(self, directory_name):
        path = self.get_directory(directory_name)
        if path and os.path.exists(path):
            return os.listdir(path)
        return []

    def add_file(self, directory_name, file_name, content):
        path = self.get_directory(directory_name)
        if path:
            with open(os.path.join(path, file_name), 'w') as file:
                file.write(content)

    def delete_file(self, directory_name, file_name):
        path = self.get_directory(directory_name)
        file_path = os.path.join(path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    def modify_file(self, directory_name, file_name, new_content):
        self.add_file(directory_name, file_name, new_content)

    def search_file(self, directory_name, file_name):
        path = self.get_directory(directory_name)
        if path is None:
            raise ValueError(f"No path found for directory name: {directory_name}")
        file_path = os.path.join(path, file_name)
        return os.path.exists(file_path)

    def get_file_path(self, directory_name, file_name):
        path = self.get_directory(directory_name)
        file_path = os.path.join(path, file_name)
        return file_path
