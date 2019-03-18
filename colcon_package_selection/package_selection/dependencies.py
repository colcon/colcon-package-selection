# Copyright 2016-2018 Dirk Thomas
# Licensed under the Apache License, Version 2.0

import argparse
import sys

from colcon_core.package_selection import logger
from colcon_core.package_selection import PackageSelectionExtensionPoint
from colcon_core.plugin_system import satisfies_version


class _DepthAndPackageNames(argparse.Action):
    """Action to assign an integer depth optional package names."""

    def __call__(self, parser, namespace, values, option_string=None):
        assert len(values) >= 1
        try:
            values[0] = int(values[0])
            if values[0] < 0:
                raise ValueError()
        except ValueError:
            raise argparse.ArgumentError(
                self, 'the first parameter must be a non-negative integer for '
                'the depth')
        setattr(namespace, self.dest, values)


class DependenciesPackageSelection(PackageSelectionExtensionPoint):
    """Select packages based on their dependencies."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            PackageSelectionExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            '--packages-up-to', nargs='*', metavar='PKG_NAME',
            help='Only process a subset of packages and their recursive '
                 'dependencies')
        parser.add_argument(
            '--packages-above', nargs='*', metavar='PKG_NAME',
            help='Only process a subset of packages and packages which '
                 'recursively depend on them')
        parser.add_argument(
            '--packages-above-depth', nargs='+',
            metavar=('DEPTH', 'PKG_NAME'), action=_DepthAndPackageNames,
            help='Only process a subset of packages and packages which '
                 'recursively depend on them up to a given depth')

        parser.add_argument(
            '--packages-select-by-dep', nargs='*', metavar='DEP_NAME',
            help='Only process packages which (recursively) depend on this')
        parser.add_argument(
            '--packages-skip-by-dep', nargs='*', metavar='DEP_NAME',
            help='Skip packages which (recursively) depend on this')
        parser.add_argument(
            '--packages-skip-up-to', nargs='*', metavar='PKG_NAME',
            help='Skip a subset of packages and their recursive dependencies')

    def check_parameters(self, args, pkg_names):  # noqa: D102
        # exit on invalid arguments
        for name in args.packages_up_to or set():
            if name not in pkg_names:
                sys.exit(
                    "Package '{name}' specified with --packages-up-to "
                    'was not found'
                    .format_map(locals()))
        for name in args.packages_above or set():
            if name not in pkg_names:
                sys.exit(
                    "Package '{name}' specified with --packages-above "
                    'was not found'
                    .format_map(locals()))
        for name in (args.packages_above_depth or [])[1:]:
            if name not in pkg_names:
                sys.exit(
                    "Package '{name}' specified with "
                    '--packages-above-depth was not found'
                    .format_map(locals()))

    def select_packages(self, args, decorators):  # noqa: D102
        if args.packages_up_to:
            select_pkgs = set(args.packages_up_to)
            for decorator in reversed(decorators):
                if decorator.descriptor.name in select_pkgs:
                    select_pkgs |= set(decorator.recursive_dependencies)
                elif decorator.selected:
                    pkg = decorator.descriptor
                    logger.info(
                        "Skipping package '{pkg.name}' in '{pkg.path}'"
                        .format_map(locals()))
                    decorator.selected = False

        if args.packages_above:
            select_pkgs = set(args.packages_above)
            for decorator in decorators:
                if decorator.descriptor.name in select_pkgs:
                    continue
                if not (select_pkgs & set(decorator.recursive_dependencies)):
                    if decorator.selected:
                        pkg = decorator.descriptor
                        logger.info(
                            "Skipping package '{pkg.name}' in '{pkg.path}'"
                            .format_map(locals()))
                        decorator.selected = False

        if args.packages_above_depth and len(args.packages_above_depth) > 1:
            depth = args.packages_above_depth[0]
            select_pkgs = set(args.packages_above_depth[1:])
            for decorator in decorators:
                if decorator.descriptor.name in select_pkgs:
                    continue
                if not [
                    d for d in set(decorator.recursive_dependencies)
                    if d in select_pkgs and d.metadata['depth'] <= depth
                ]:
                    if decorator.selected:
                        pkg = decorator.descriptor
                        logger.info(
                            "Skipping package '{pkg.name}' in '{pkg.path}'"
                            .format_map(locals()))
                        decorator.selected = False

        if args.packages_select_by_dep:
            deps = set(args.packages_select_by_dep)
            for decorator in decorators:
                if not (deps & set(decorator.recursive_dependencies)):
                    if decorator.selected:
                        pkg = decorator.descriptor
                        logger.info(
                            "Skipping package '{pkg.name}' in '{pkg.path}'"
                            .format_map(locals()))
                        decorator.selected = False

        if args.packages_skip_by_dep:
            deps = set(args.packages_skip_by_dep)
            for decorator in decorators:
                if deps & set(decorator.recursive_dependencies):
                    if decorator.selected:
                        pkg = decorator.descriptor
                        logger.info(
                            "Skipping package '{pkg.name}' in '{pkg.path}'"
                            .format_map(locals()))
                        decorator.selected = False

        if args.packages_skip_up_to:
            skip_pkgs = set(args.packages_skip_up_to)
            for decorator in reversed(decorators):
                if decorator.descriptor.name in skip_pkgs:
                    skip_pkgs |= set(decorator.recursive_dependencies)
                    if decorator.selected:
                        pkg = decorator.descriptor
                        logger.info(
                            "Skipping package '{pkg.name}' in '{pkg.path}'"
                            .format_map(locals()))
                        decorator.selected = False
