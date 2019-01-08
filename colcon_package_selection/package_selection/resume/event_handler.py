# Copyright 2019 Dirk Thomas
# Licensed under the Apache License, Version 2.0

from colcon_core.event.job import JobEnded
from colcon_core.event.job import JobStarted
from colcon_core.event_handler import EventHandlerExtensionPoint
from colcon_core.event_reactor import EventReactorShutdown
from colcon_core.location import get_log_path
from colcon_core.location import get_previous_log_path
from colcon_core.plugin_system import satisfies_version
from colcon_package_selection.package_selection.resume \
    import RESUME_LOG_FILENAME


class LogFinishedEventHandler(EventHandlerExtensionPoint):
    """
    Write a log file containing all successfully built job names.

    The log file `resume.log` is created in the log directory and contains all
    successfully built job names as well as the ones from the log file of the
    previous build of the same verb.

    The extension handles events of the following types:
    - :py:class:`colcon_core.event.job.JobEnded`
    - :py:class:`colcon_core.event.job.JobStarted`
    - :py:class:`colcon_core.event_reactor.EventReactorShutdown`
    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            EventHandlerExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')
        self._finished_names = None

    def __call__(self, event):  # noqa: D102
        data = event[0]

        self._init_finished_names()

        if isinstance(data, JobStarted):
            self._finished_names.discard(data.identifier)

        elif isinstance(data, JobEnded):
            if not data.rc:
                self._finished_names.add(data.identifier)

        elif isinstance(data, EventReactorShutdown):
            filename = get_log_path() / RESUME_LOG_FILENAME
            with filename.open(mode='w') as h:
                h.write(
                    '# Finished packages, either from this invocation or from '
                    'previous invocations\n')
                for name in sorted(self._finished_names):
                    h.write(name + '\n')

    def _init_finished_names(self):
        if self._finished_names is not None:
            return

        self._finished_names = set()

        # look for a log file from the previous invocation
        previous_log_path = get_previous_log_path(get_log_path())
        if previous_log_path:
            previous_filename = previous_log_path / RESUME_LOG_FILENAME
            if previous_filename.exists():
                lines = previous_filename.read_text().splitlines()
                for line in lines:
                    if line.startswith('#'):
                        continue
                    self._finished_names.add(line)
