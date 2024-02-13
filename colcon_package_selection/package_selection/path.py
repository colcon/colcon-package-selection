# Copyright 2024 Open Source Robotics Foundation, Inc.
# Licensed under the Apache License, Version 2.0

from pathlib import Path

from colcon_core.package_selection import logger
from colcon_core.package_selection import PackageSelectionExtensionPoint
from colcon_core.plugin_system import satisfies_version


class PathPackageSelectionExtension(PackageSelectionExtensionPoint):
    """Select a set of packages based on their path."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            PackageSelectionExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            '--packages-select-under-path', nargs='*',
            metavar='DIRECTORY_PATH', type=Path,
            help='Only process a subset of packages which are located in '
                 'a specified directory or a subdirectory thereof.')

    def check_parameters(self, args, pkg_names):  # noqa: D102
        for path in args.packages_select_under_path or []:
            if not path.is_dir():
                logger.warning(
                    "ignoring non-existent directory '{path}' in "
                    '--packages-select-under-path'.format_map(locals()))

    def select_packages(self, args, decorators):  # noqa: D102
        if args.packages_select_under_path:
            packages_select_under_path = {
                path for path in args.packages_select_under_path
                if path.is_dir()
            }
            for decorator in decorators:
                # skip packages which have already been ruled out
                if not decorator.selected:
                    continue

                pkg_path = Path(decorator.descriptor.path)
                if pkg_path not in packages_select_under_path and not any(
                    path in pkg_path.parents
                    for path in args.packages_select_under_path
                ):
                    decorator.selected = False
