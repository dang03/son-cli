import logging
import sys
import os
import yaml

from son.workspace.project import Project

log = logging.getLogger(__name__)


class Workspace:

    # Parameter strings for the configuration descriptor.
    CONFIG_STR_NAME = "name"
    CONFIG_STR_CATALOGUES_DIR = "catalogues_dir"
    CONFIG_STR_CATALOGUE_NS_DIR = "ns_catalogue"
    CONFIG_STR_CATALOGUE_VNF_DIR = "vnf_catalogue"
    CONFIG_STR_CONFIG_DIR = "configuration_dir"
    CONFIG_STR_PLATFORMS_DIR = "platforms_dir"
    CONFIG_STR_PROJECTS_DIR = "projects_dir"

    __descriptor_name__ = "workspace.yml"

    def __init__(self, ws_root, ws_name='SONATA workspace', catalogues_dir='catalogues',
                 config_dir='configuration', platform_dir='platforms'):
        #logging.basicConfig(level=logging.INFO)
        self._log = logging.getLogger(__name__)
        self.ws_root = ws_root
        self.ws_name = ws_name
        self.dirs = dict()
        self.dirs[self.CONFIG_STR_CATALOGUES_DIR] = catalogues_dir
        self.dirs[self.CONFIG_STR_CONFIG_DIR] = config_dir
        self.dirs[self.CONFIG_STR_PLATFORMS_DIR] = platform_dir

        # Sub-directories of catalogues
        self.dirs[self.CONFIG_STR_CATALOGUE_NS_DIR] = \
            os.path.join(self.dirs[self.CONFIG_STR_CATALOGUES_DIR], self.CONFIG_STR_CATALOGUE_NS_DIR)
        self.dirs[self.CONFIG_STR_CATALOGUE_VNF_DIR] = \
            os.path.join(self.dirs[self.CONFIG_STR_CATALOGUES_DIR], self.CONFIG_STR_CATALOGUE_VNF_DIR)

        # Projects dir (optional)
        self.dirs[self.CONFIG_STR_PROJECTS_DIR] = 'projects'

    def create_dirs(self):
        """
        Create the base directory structure for the workspace
        Invoked upon workspace creation.
        :return:
        """

        self._log.info('Creating workspace at %s', self.ws_root)
        os.makedirs(self.ws_root, exist_ok=False)
        for d in self.dirs:
            path = os.path.join(self.ws_root, self.dirs[d])
            os.makedirs(path, exist_ok=True)

    def create_catalog_sample(self):
        d = {'name': 'My personal catalog',
             'credentials': 'personal'
             }

        ws_file_path = os.path.join(self.ws_root, self.dirs[self.CONFIG_STR_CATALOGUES_DIR], 'personal.yml')
        with open(ws_file_path, 'w') as ws_file:
            ws_file.write(yaml.dump(d, default_flow_style=False))

    def create_ws_descriptor(self):
        """
        Creates a workspace configuration file descriptor.
        This is triggered by workspace creation and configuration changes.
        :return:
        """
        d = {'version': '0.01',  # should we version the workspace
             self.CONFIG_STR_NAME: self.ws_name,
             self.CONFIG_STR_CATALOGUES_DIR: self.dirs[self.CONFIG_STR_CATALOGUES_DIR],
             self.CONFIG_STR_CONFIG_DIR: self.dirs[self.CONFIG_STR_CONFIG_DIR],
             self.CONFIG_STR_PLATFORMS_DIR: self.dirs[self.CONFIG_STR_PLATFORMS_DIR]
             }

        ws_file_path = os.path.join(self.ws_root, Workspace.__descriptor_name__)
        with open(ws_file_path, 'w') as ws_file:
            yaml.dump(d, ws_file, default_flow_style=False)

    def create_files(self):
        self.create_ws_descriptor()
        self.create_catalog_sample()

    def check_ws_exists(self):
        ws_file = os.path.join(self.ws_root, Workspace.__descriptor_name__)
        return os.path.exists(ws_file) or os.path.exists(self.ws_root)

    @staticmethod
    def __create_from_descriptor__(ws_root):
        """
        Creates a Workspace object based on a configuration descriptor
        :param ws_root: base path of the workspace
        :return: Workspace object
        """
        ws_filename = os.path.join(ws_root, Workspace.__descriptor_name__)
        if not os.path.isdir(ws_root) or not os.path.isfile(ws_filename):
            log.error("Unable to load workspace descriptor '{}'".format(ws_filename))
            return None

        ws_file = open(ws_filename)
        ws_config = yaml.load(ws_file)

        return Workspace(ws_root,
                         ws_name=ws_config[Workspace.CONFIG_STR_NAME],
                         catalogues_dir=ws_config[Workspace.CONFIG_STR_CATALOGUES_DIR],
                         config_dir=ws_config[Workspace.CONFIG_STR_CONFIG_DIR],
                         platform_dir=ws_config[Workspace.CONFIG_STR_PLATFORMS_DIR])


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate new sonata workspaces and project layouts")
    parser.add_argument("--init", help="Create a new sonata workspace on the specified location", action="store_true")
    parser.add_argument("--workspace", help="location of existing (or new) workspace", required=True)
    parser.add_argument("--project",
                        help="create a new project at the specified location", required=False)

    log.debug("parsing arguments")
    args = parser.parse_args()
    ws_root = os.path.expanduser(args.workspace)
    ws = Workspace(ws_root)

    if args.init:
        if ws.check_ws_exists():
            print("A workspace already exists at the specified location, exiting", file=sys.stderr)
            return
        log.debug("Attempting to create a new workspace")
        cwd = os.getcwd()
        ws.create_dirs()
        ws.create_files()
        os.chdir(cwd)
        log.debug("Workspace created.")
    else:
        if not ws.check_ws_exists():
            print("Could not find a SONATA workspace at the specified location", file=sys.stderr)
            return

    if args.project is not None:
        log.debug("Attempting to create a new project")
        prj_root = os.path.expanduser(args.project)
        proj = Project(prj_root, ws_root)
        proj.create_prj()
        log.debug("Project created.")
