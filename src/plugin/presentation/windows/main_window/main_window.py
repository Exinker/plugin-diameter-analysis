from collections.abc import Mapping

from PySide6 import QtCore, QtWidgets

from plugin.configs import DIAMETER_HISTOGRAM_CONFIG
from plugin.context import HistogramData
from plugin.managers.state_manager import StateManager
from plugin.presentation.windows.main_window.central_widget import CentralWidget
from spectrumapp.windows.main_window import BaseMainWindow


class MainWindow(BaseMainWindow):

    def __init__(
        self,
        state_manager: StateManager,
        flags: Mapping[QtCore.Qt.WindowType, bool] | None = None,
    ) -> None:
        super().__init__()
        self.state_manager = state_manager

        # title
        self.setWindowTitle('Diameter Analysis')

        # flags
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        flags = flags or {
            QtCore.Qt.WindowType.Window: True,
            QtCore.Qt.WindowType.WindowStaysOnTopHint: True,
        }
        for key, value in flags.items():
            self.setWindowFlag(key, value)

        # widget
        widget = CentralWidget(
            config=DIAMETER_HISTOGRAM_CONFIG,
            parent=self,
        )
        self.setCentralWidget(widget)

        # geometry
        self.adjustSize()

        window_size = self.minimumSizeHint()
        window_width = window_size.width() + 20
        window_height = window_size.height() + 20

        screen = self.screen() or QtWidgets.QApplication.primaryScreen()
        if screen is None:
            self.resize(window_width, window_height)
        else:
            available = screen.availableGeometry()
            x = available.x() + max(0, available.width() - window_width - 20)
            y = available.y() + 20
            self.setGeometry(x, y, window_width, window_height)

    def on_refreshed(self, *args, **kwargs) -> None:
        histogram = self.state_manager.build_histogram()
        self.refresh(histogram=histogram)

    def refresh(
        self,
        histogram: HistogramData,
    ) -> None:
        self.centralWidget().diameter_widget.plot(histogram=histogram)
