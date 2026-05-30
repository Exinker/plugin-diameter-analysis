import logging
import sys
import time

from PySide6 import QtWidgets

from plugin.exceptions import exception_wrapper
from plugin.managers.data_source_manager import DataSourceManager
from plugin.managers.diameter_manager import DiameterManager
from plugin.managers.state_manager import StateManager
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

    @exception_wrapper
    def run(self) -> int:
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

        self.window = MainWindow(state_manager=self.state_manager)
        self.window.show()

        event_id = ''
        self.window.refresh(
            event_id=event_id,
            histogram=self.state_manager.build_histogram(
                event_id=event_id,
                force=True,
            ),
        )

        sys.modules['__main__'].on_atom_event = self.on_atom_event

        self.app.exec()

    def on_atom_event(self, event_type, event_code, event_pv):

        event_id = str(time.perf_counter_ns())

        if event_code in [
            28,  # CU_CURRENT_PEAK_CHANGED
        ] and event_type == 'window':
            LOGGER.info(
                'On Atom event',
                extra=dict(
                    event_id=event_id,
                    event_type=event_type,
                    event_code=event_code,
                    event_pv=event_pv,
                ),
            )
            self.window.on_refreshed(event_id=event_id)

            return None

        if event_code in [
            69,  # CU_CURRENT_PROBE_CHANGED
        ] and event_type == 'window':
            LOGGER.info(
                'On Atom event',
                extra=dict(
                    event_id=event_id,
                    event_type=event_type,
                    event_code=event_code,
                    event_pv=event_pv,
                ),
            )
            self.window.on_refreshed(event_id=event_id)

            return None

        if event_code in [
            110,  # CU_CLOSE_APP
            130,  # CU_IS_ABOUT_CLOSE_DOCUMENT
            138,  # CU_IS_ABOUT_CLOSE_APP
        ]:
            LOGGER.info(
                'On Atom event',
                extra=dict(
                    event_id=event_id,
                    event_type=event_type,
                    event_code=event_code,
                    event_pv=event_pv,
                ),
            )
            self.window.close()
            self.app.quit()

            return None
