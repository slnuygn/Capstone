import json
import os
import re
from typing import List

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


DEFAULT_CONV_LAYERS = [
    {"inChannels": 3, "outChannels": 32, "kernelSize": 3, "padding": 1},
] + [
    {"inChannels": 64, "outChannels": 128, "kernelSize": 5, "padding": 2}
    for _ in range(12)
]


class ClassificationConfig(QObject):
    """Persist and expose classification layer configuration to QML."""

    configChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        self._config_path = os.path.join(
            self._project_root, "features", "classification", "conv_layers.json"
        )
        self._classification_qml_path = os.path.join(
            self._project_root,
            "features",
            "classification",
            "ui",
            "classification_page.qml",
        )
        self._conv_layers: List[dict] = []
        self._load_config()
        self._ensure_min_layers(len(DEFAULT_CONV_LAYERS))

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        if self._load_from_qml():
            return
        if self._load_from_json():
            return
        self._conv_layers = [layer.copy() for layer in DEFAULT_CONV_LAYERS]

    def _load_from_json(self) -> bool:
        if not os.path.exists(self._config_path):
            return False

        try:
            with open(self._config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return False

        if not isinstance(data, list):
            return False

        sanitized = []
        for entry in data:
            if not isinstance(entry, dict):
                sanitized.append(
                    DEFAULT_CONV_LAYERS[len(sanitized) % len(DEFAULT_CONV_LAYERS)].copy()
                )
                continue
            sanitized.append(
                {
                    "inChannels": int(entry.get("inChannels", 0)),
                    "outChannels": int(entry.get("outChannels", 0)),
                    "kernelSize": int(entry.get("kernelSize", 0)),
                    "padding": int(entry.get("padding", 0)),
                }
            )

        self._conv_layers = sanitized
        return True

    def _load_from_qml(self) -> bool:
        if not os.path.exists(self._classification_qml_path):
            return False

        try:
            with open(self._classification_qml_path, "r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError:
            return False

        layers = []
        inside_layer = False
        current = {"inChannels": 0, "outChannels": 0, "kernelSize": 0, "padding": 0}

        for raw_line in lines:
            stripped = raw_line.strip()
            if stripped.startswith("ConvolutionalLayer2D") and "{" in stripped:
                inside_layer = True
                current = {"inChannels": 0, "outChannels": 0, "kernelSize": 0, "padding": 0}
                continue

            if inside_layer:
                if stripped.startswith("inChannels:"):
                    current["inChannels"] = self._extract_numeric(stripped)
                elif stripped.startswith("outChannels:"):
                    current["outChannels"] = self._extract_numeric(stripped)
                elif stripped.startswith("kernelSize:"):
                    current["kernelSize"] = self._extract_numeric(stripped)
                elif stripped.startswith("padding:"):
                    current["padding"] = self._extract_numeric(stripped)
                elif stripped == "}":
                    layers.append(current.copy())
                    inside_layer = False

        if not layers:
            return False

        self._conv_layers = layers
        return True

    @staticmethod
    def _extract_numeric(line: str) -> int:
        match = re.search(r"-?\d+", line)
        if not match:
            return 0
        return int(match.group(0))

    def _ensure_min_layers(self, minimum: int) -> None:
        while len(self._conv_layers) < minimum:
            template_index = len(self._conv_layers)
            template = (
                DEFAULT_CONV_LAYERS[template_index]
                if template_index < len(DEFAULT_CONV_LAYERS)
                else DEFAULT_CONV_LAYERS[-1]
            )
            self._conv_layers.append(template.copy())

    def _save_config(self) -> None:
        self._write_json()
        self._write_layers_to_qml()

    def _write_json(self) -> None:
        try:
            with open(self._config_path, "w", encoding="utf-8") as handle:
                json.dump(self._conv_layers, handle, indent=2)
        except OSError as exc:
            print(f"Failed to persist classification configuration: {exc}")

    def _write_layers_to_qml(self) -> None:
        if not os.path.exists(self._classification_qml_path):
            return

        try:
            with open(self._classification_qml_path, "r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError:
            return

        output_lines = []
        layer_idx = -1
        inside_layer = False

        for raw_line in lines:
            stripped = raw_line.strip()
            if stripped.startswith("ConvolutionalLayer2D") and "{" in stripped:
                layer_idx += 1
                inside_layer = True
                output_lines.append(raw_line)
                continue

            if inside_layer and 0 <= layer_idx < len(self._conv_layers):
                output_lines.append(
                    self._maybe_replace_property_line(raw_line, stripped, layer_idx)
                )
                if stripped == "}":
                    inside_layer = False
                continue

            output_lines.append(raw_line)

        try:
            with open(self._classification_qml_path, "w", encoding="utf-8") as handle:
                handle.writelines(output_lines)
        except OSError as exc:
            print(f"Failed to update classification_page.qml: {exc}")

    def _maybe_replace_property_line(self, raw_line: str, stripped: str, layer_idx: int) -> str:
        layer = self._conv_layers[layer_idx]
        for key in ("inChannels", "outChannels", "kernelSize", "padding"):
            if stripped.startswith(f"{key}:"):
                prefix, _ = raw_line.split(":", 1)
                return f"{prefix}: {layer[key]}\n"
        return raw_line

    # ------------------------------------------------------------------
    # Slots exposed to QML
    # ------------------------------------------------------------------

    @pyqtSlot(result="QVariantList")
    def getConvLayers(self):
        return [layer.copy() for layer in self._conv_layers]

    @pyqtSlot(int, int, int, int, int)
    def updateConvLayer(self, layer_index: int, in_channels: int, out_channels: int, kernel_size: int, padding: int) -> None:
        if layer_index < 0:
            return

        self._ensure_min_layers(layer_index + 1)

        self._conv_layers[layer_index] = {
            "inChannels": int(in_channels),
            "outChannels": int(out_channels),
            "kernelSize": int(kernel_size),
            "padding": int(padding),
        }
        self._save_config()
        self.configChanged.emit()

    @pyqtSlot()
    def resetToDefaults(self) -> None:
        self._conv_layers = [layer.copy() for layer in DEFAULT_CONV_LAYERS]
        self._save_config()
        self.configChanged.emit()
