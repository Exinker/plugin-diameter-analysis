import logging
import sys

from PySide6 import QtWidgets

from plugin.controllers import AtomEventHandler
from plugin.exceptions import exception_wrapper
from plugin.managers.data_source_manager import DataSourceManager
from plugin.managers.diameter_manager import DiameterManager
from plugin.managers.state_manager import StateManager
from plugin.models.events import CloseEvent, RefreshEvent
from plugin.presentation.windows import MainWindow

LOGGER = logging.getLogger('plugin-diameter-analysis')


class Plugin:

    def __init__(
        self,
        data_source_manager: DataSourceManager,
        diameter_manager: DiameterManager,
        state_manager: StateManager,
    ) -> None:

        self.data_source_manager = data_source_manager
        self.diameter_manager = diameter_manager
        self.state_manager = state_manager

    def setup(self) -> None:
        event_id = 'setup'

        self.window.show()
        self.window.refresh(
            event_id=event_id,
            histogram=self.state_manager.build_histogram(
                event_id=event_id,
                force=True,
            ),
        )

        self.atom_event_handler = AtomEventHandler(
            on_refresh=self.on_refresh,
            on_close=self.on_close,
        )
        sys.modules['__main__'].on_atom_event = self.atom_event_handler.on_atom_event

    @exception_wrapper
    def run(self) -> int:

        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        self.window = MainWindow()

        self.setup()

        self.app.exec()

    def on_refresh(self, event: RefreshEvent) -> None:

        LOGGER.info(
            'On refresh event',
            extra=dict(
                event_id=event.id,
            ),
        )
        histogram = self.state_manager.build_histogram(
            event_id=event.id,
        )
        self.window.refresh(
            event_id=event.id,
            histogram=histogram,
        )

    def on_close(self, event: CloseEvent) -> None:

        LOGGER.info(
            'On close event',
            extra=dict(
                event_id=event.id,
            ),
        )
        self.window.close()
        self.app.quit()
