# Copyright 2019 Dirk Thomas
# Licensed under the Apache License, Version 2.0

from colcon_core.location import get_log_path
from colcon_core.location import get_previous_log_path
from colcon_core.package_selection import logger
from colcon_core.package_selection import PackageSelectionExtensionPoint
from colcon_core.plugin_system import satisfies_version
from colcon_package_selection.package_selection.resume \
    import RESUME_LOG_FILENAME


class SkipPreviousPackageSelectionExtension(PackageSelectionExtensionPoint):
    """Skip a set of packages based on previous invocations."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            PackageSelectionExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            '--packages-skip-previously-finished', action='store_true',
            help='Skip a set of packages which have been completed in a '
                 'previous invocation')

    def check_parameters(self, args, pkg_names):  # noqa: D102
        if not args.packages_skip_previously_finished:
            return

        # check that the log file from a previous invocation can be found
        previous_log_path = get_previous_log_path(get_log_path())
        if previous_log_path:
            previous_filename = previous_log_path / RESUME_LOG_FILENAME
            if not previous_filename.exists():
                logger.warning(
                    "Failed to find '{previous_filename}' log file from a "
                    'previous invocation, ignoring '
                    "'--packages-skip-previously-finished'"
                    .format_map(locals()))

    def select_packages(self, args, decorators):  # noqa: D102
        if not args.packages_skip_previously_finished:
            return

        # collect names of previously finished packages
        previous_log_path = get_previous_log_path(get_log_path())
        if not previous_log_path:
            return

        previous_filename = previous_log_path / RESUME_LOG_FILENAME
        if not previous_filename.exists():
            return

        lines = previous_filename.read_text().splitlines()
        names = [l for l in lines if not l.startswith('#')]

        for decorator in decorators:
            # skip packages which have already been ruled out
            if not decorator.selected:
                continue

            pkg = decorator.descriptor

            # skip packages which have previously finished
            if pkg.name in names:
                logger.info(
                    "Skipping previously finished package '{pkg.name}' in "
                    "'{pkg.path}'".format_map(locals()))
                decorator.selected = False
