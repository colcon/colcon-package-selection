# Copyright 2016-2018 Dirk Thomas
# Licensed under the Apache License, Version 2.0

import sys

from colcon_core.package_selection import logger
from colcon_core.package_selection import PackageSelectionExtensionPoint
from colcon_core.plugin_system import satisfies_version


class StartEndPackageSelection(PackageSelectionExtensionPoint):
    """Select a range of packages based on flattened topological ordering."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            PackageSelectionExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            '--package-start', metavar='PKG_NAME',
            help='Skip packages before this in flat topological ordering')
        parser.add_argument(
            '--package-end', metavar='PKG_NAME',
            help='Skip packages after this in flat topological ordering')

    def check_parameters(self, args, pkg_names):  # noqa: D102
        # exit on invalid arguments
        if args.package_start and args.package_start not in pkg_names:
            sys.exit(
                "Package '{args.package_start}' specified with "
                '--package-start was not found'
                .format_map(locals()))
        if args.package_end and args.package_end not in pkg_names:
            sys.exit(
                "Package '{args.package_end}' specified with --package-end "
                'was not found'
                .format_map(locals()))

    def select_packages(self, args, decorators):  # noqa: D102
        pkg_within_range = not args.package_start
        for decorator in decorators:
            pkg = decorator.descriptor

            # identify start of range
            if pkg.name == args.package_start:
                pkg_within_range = True

            selected = pkg_within_range
            if decorator.selected and not selected:
                # mark packages outside of the range as not selected
                logger.info(
                    "Skipping package '{pkg.name}' in '{pkg.path}'"
                    .format_map(locals()))
                decorator.selected = False

            # identify end of range
            if pkg.name == args.package_end:
                if not pkg_within_range:
                    sys.exit(
                        "The --package-end package '{args.package_end}' "
                        'occurs topologically before the --package-start '
                        "package '{args.package_start}'"
                        .format_map(locals()))
                pkg_within_range = False
