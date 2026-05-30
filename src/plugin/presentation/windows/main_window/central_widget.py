import json
import logging

import numpy as np
from PySide6 import QtWidgets

from plugin.configs import DiameterHistogramConfig, HistogramUnits
from plugin.context import HistogramData
from spectrumapp.widgets.graph_widget import BaseGraphWidget


LOGGER = logging.getLogger('plugin-diameter-analysis')


class DiameterDistributionWidget(BaseGraphWidget):

    def __init__(
        self,
        config: DiameterHistogramConfig,
        parent=None,
    ):
        super().__init__(parent=parent)

        self._config = config

    def plot(
        self,
        event_id: str,
        histogram: HistogramData,
    ) -> None:
        LOGGER.info(
            'Plot histogram',
            extra=dict(
                event_id=event_id,
                config=self._config.model_dump(),
                data=histogram.to_dict(),
            ),
        )

        counts = histogram.counts
        edges = histogram.edges
        centers = np.arange(len(counts))

        ax = self.canvas.axes
        ax.cla()

        total = np.sum(counts)
        values = {
            HistogramUnits.COUNTS: counts,
            HistogramUnits.PERCENTS: 100 * counts / total if total > 0 else np.zeros_like(counts, dtype=float),
        }[self._config.units]

        ax.bar(
            centers,
            values,
            width=self._config.bin_width,
            edgecolor=self._config.edge_color,
            facecolor=self._config.face_color,
            align='center',
        )

        ax.set_xticks(centers)
        if self._config.labels is None:
            xticklabels = np.convolve(edges, [0.5, 0.5], mode='valid')
        else:
            xticklabels = self._config.labels
        ax.set_xticklabels(
            xticklabels,
            rotation=0,
            ha='center',
        )

        ax.set_xlabel(
            'μm',
            labelpad=2,
        )
        ax.xaxis.set_label_coords(1.05, -0.04)
        ax.xaxis.label.set_horizontalalignment('right')

        ax.set_ylabel(
            '%' if self._config.units == HistogramUnits.PERCENTS else '',
            labelpad=2,
            # rotation=0,
        )
        # ax.yaxis.set_label_coords(-0.05, 1.0)
        # ax.yaxis.label.set_horizontalalignment('left')
        # ax.yaxis.label.set_verticalalignment('bottom')

        ax.set_xlim(-0.5, len(counts) - 0.5)
        ax.set_ylim(0, None)

        ax.relim()
        ax.autoscale_view(scalex=False, scaley=True)

        # self.canvas.figure.tight_layout(pad=0.4)
        self.canvas.draw()


class CentralWidget(QtWidgets.QWidget):

    def __init__(
        self,
        *args,
        config: DiameterHistogramConfig,
        parent: QtWidgets.QWidget | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, parent=parent, **kwargs)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.diameter_widget = DiameterDistributionWidget(
            config=config,
        )
        layout.addWidget(self.diameter_widget, 1)
