import logging
import sys

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
        self.window.refresh(
            histogram=self.state_manager.build_histogram(force=True),
        )

        sys.modules['__main__'].on_atom_event = self.on_atom_event

        self.app.exec()

    def on_atom_event(self, event_type, event_code, event_pv):

        if event_code in [
            # 68,  # CU_UPDATE_TA
            69,  # CU_CURRENT_PROBE_CHANGED
            # 72,  # CU_TABLE_SELCHANGED
        ] and event_type == 'support':
            LOGGER.info(
                'Atom event: type %s, code %s, pv %s', event_type, event_code, event_pv,
            )
            self.window.on_refreshed()

            return None

        if event_code in [
            110,  # CU_CLOSE_APP
            130,  # CU_IS_ABOUT_CLOSE_DOCUMENT
            138,  # CU_IS_ABOUT_CLOSE_APP
        ]:
            LOGGER.info(
                'Atom event: type %s, code %s, pv %s', event_type, event_code, event_pv,
            )
            self.window.close()
            self.app.quit()

            return None
