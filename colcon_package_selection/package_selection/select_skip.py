# Copyright 2016-2018 Dirk Thomas
# Licensed under the Apache License, Version 2.0

import re

from colcon_core.package_selection import logger
from colcon_core.package_selection import PackageSelectionExtensionPoint
from colcon_core.plugin_system import satisfies_version


class WhitelistBlacklistPackageSelectionExtension(
    PackageSelectionExtensionPoint
):
    """Select a set of packages based on a whitelist / blacklist."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            PackageSelectionExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            '--package-whitelist', nargs='*', metavar='PKG_NAME',
            help='Only process a subset of packages')
        parser.add_argument(
            '--package-blacklist', nargs='*', metavar='PKG_NAME',
            help='Skip a set of packages')

        parser.add_argument(
            '--package-whitelist-regex', nargs='*', metavar='PATTERN',
            help='Only process a subset of packages where any of the patterns '
                 'match the package name')
        parser.add_argument(
            '--package-blacklist-regex', nargs='*', metavar='PATTERN',
            help='Skip a set of packages where any of the patterns match the '
                 'package name')

    def check_parameters(self, args, pkg_names):  # noqa: D102
        # warn about ignored arguments
        for pkg_name in args.package_whitelist or []:
            if pkg_name not in pkg_names:
                logger.warn(
                    "ignoring unknown package '{pkg_name}' in "
                    '--package-whitelist'.format_map(locals()))

        for pkg_name in args.package_blacklist or []:
            if pkg_name not in pkg_names:
                logger.warn(
                    "ignoring unknown package '{pkg_name}' in "
                    '--package-blacklist'.format_map(locals()))

        for pattern in list(args.package_whitelist_regex or []):
            # check patterns and remove invalid ones
            try:
                re.compile(pattern)
            except Exception as e:
                logger.warn(
                    "the --package-whitelist-regex '{pattern}' failed to "
                    'compile: {e}'.format_map(locals()))
                args.package_whitelist_regex.remove(pattern)
                continue

            if not any(re.match(pattern, pkg_name) for pkg_name in pkg_names):
                logger.warn(
                    "the --package-whitelist-regex '{pattern}' doesn't match "
                    'any of the package names'.format_map(locals()))

        for pattern in list(args.package_blacklist_regex or []):
            # check patterns and remove invalid ones
            try:
                re.compile(pattern)
            except Exception as e:
                logger.warn(
                    "the --package-blacklist-regex '{pattern}' failed to "
                    'compile: {e}'.format_map(locals()))
                args.package_blacklist_regex.remove(pattern)
                continue

            if not any(re.match(pattern, pkg_name) for pkg_name in pkg_names):
                logger.warn(
                    "the --package-blacklist-regex '{pattern}' doesn't match "
                    'any of the package names'.format_map(locals()))

    def select_packages(self, args, decorators):  # noqa: D102
        for decorator in decorators:
            # skip packages which have already been ruled out
            if not decorator.selected:
                continue

            pkg = decorator.descriptor

            if (
                pkg.name in (args.package_blacklist or []) or
                any(
                    re.match(pattern, pkg.name)
                    for pattern in (args.package_blacklist_regex or [])
                )
            ):
                logger.info(
                    "Skipping blacklisted package '{pkg.name}' in '{pkg.path}'"
                    .format_map(locals()))
                decorator.selected = False

            elif (
                args.package_whitelist is not None or
                args.package_whitelist_regex is not None
            ):
                if (
                    pkg.name not in (args.package_whitelist or []) and
                    not any(
                        re.match(pattern, pkg.name)
                        for pattern in (args.package_whitelist_regex or [])
                    )
                ):
                    logger.info(
                        "Skipping not whitelisted package '{pkg.name}' in "
                        "'{pkg.path}'".format_map(locals()))
                    decorator.selected = False
