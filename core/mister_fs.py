#!/usr/bin/env python

import logging
import os
import shutil

logging.basicConfig(level=logging.INFO)

parameters = {}
from jinja2 import Environment, FileSystemLoader

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '../templates')),
    trim_blocks=False)

client = None


def generate_template(input_file, context):
    output = TEMPLATE_ENVIRONMENT.get_template(input_file).render(context)
    return output


def generate_template_file(input_file, output_file, context):
    output = generate_template(input_file, context)
    with open(output_file, "w") as f:
        f.write(output)
    return True


class MisterFs:

    def __init__(self, path=None):
        self.path = "tmp" if not path else path
        self._init_folder()
        pass

    def _init_folder(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            os.chmod(self.path, 0o777)

    def list_files(self, given_path):
        path = "%s/%s" % (self.path, given_path)
        if os.path.exists(path):
            if os.path.isfile(path):
                filename = given_path.split("/")[-1]
                return [filename]
            else:
                return os.listdir(path)
        else:
            return []

    def create_file(self, given_path, data):
        path = "%s/%s" % (self.path, given_path)
        # Delete file if it already exists
        if os.path.exists(path):
            os.remove(path)
        # Write data in a new file
        with open(path, "a") as f:
            f.write(data)
        return True

    def load_file(self, given_path):
        path = "%s/%s" % (self.path, given_path)
        with open(path, "r") as content_file:
            content = content_file.read()
        return content

    def delete_file(self, given_path, is_folder=False):
        path = "%s/%s" % (self.path, given_path)
        status_code = 0
        if os.path.exists(path):
            if not is_folder:
                status_code = os.remove(path)
            else:
                if given_path != "":
                    status_code = shutil.rmtree(path)
        return status_code

    def create_folder(self, given_path):
        path = "%s/%s" % (self.path, given_path)
        return os.makedirs(path)

    def run_file(self, given_path):
        cmd = "pushd %s; chmod +x %s; ./%s; popd" % (self.path, given_path, given_path)
        return os.system(cmd)


if __name__ == "__main__":
    fs_manager = MisterFs()
    print(fs_manager.list_files())
    fs_manager.clean_folder()
    print(fs_manager.list_files())
    fs_manager.create_file("toto", "foo")
    fs_manager.create_file("tata", "bar")
    print(fs_manager.list_files())
    for file_name in fs_manager.list_files():
        print(fs_manager.load_file(file_name))
