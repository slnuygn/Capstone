import ast
import os
import pprint
import re
from typing import List

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


DEFAULT_CONV_LAYERS = [
    {"inChannels": 3, "outChannels": 32, "kernelSize": 3, "padding": 0},
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
        self._classification_qml_path = os.path.join(
            self._project_root,
            "features",
            "classification",
            "ui",
            "classification_page.qml",
        )
        self._classification_python_path = os.path.join(
            self._project_root,
            "features",
            "classification",
            "python",
            "classifier_prototype.py",
        )
        self._conv_layers: List[dict] = []
        self._load_config()
        self._ensure_min_layers(len(DEFAULT_CONV_LAYERS))

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        if self._load_from_python():
            return
        if self._load_from_qml():
            return
        self._conv_layers = [layer.copy() for layer in DEFAULT_CONV_LAYERS]

    def _load_from_python(self) -> bool:
        if not os.path.exists(self._classification_python_path):
            return False

        try:
            with open(self._classification_python_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except OSError:
            return False

        marker = "CONV_LAYER_SPEC"
        start = content.find(marker)
        if start == -1:
            return False

        list_start = content.find("[", start)
        if list_start == -1:
            return False

        depth = 0
        list_end = None
        for idx in range(list_start, len(content)):
            char = content[idx]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    list_end = idx + 1
                    break

        if list_end is None:
            return False

        list_text = content[list_start:list_end]

        try:
            parsed = ast.literal_eval(list_text)
        except (SyntaxError, ValueError):
            return False

        if not isinstance(parsed, list):
            return False

        sanitized = []
        for entry in parsed:
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
        self._write_layers_to_qml()
        self._write_layers_to_python()

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

    def _write_layers_to_python(self) -> None:
        if not os.path.exists(self._classification_python_path):
            return

        try:
            with open(self._classification_python_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except OSError:
            return

        marker = "CONV_LAYER_SPEC"
        start = content.find(marker)
        if start == -1:
            return

        list_start = content.find("[", start)
        if list_start == -1:
            return

        depth = 0
        list_end = None
        for idx in range(list_start, len(content)):
            char = content[idx]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    list_end = idx + 1
                    break

        if list_end is None:
            return

        block_end = list_end
        while block_end < len(content):
            if content[block_end] in " \t":
                block_end += 1
                continue
            if content[block_end] == "\n":
                block_end += 1
                continue
            if content.startswith("= [", block_end):
                eq_list_start = content.find("[", block_end)
                if eq_list_start == -1:
                    break

                depth = 0
                eq_list_end = None
                for idx in range(eq_list_start, len(content)):
                    char = content[idx]
                    if char == "[":
                        depth += 1
                    elif char == "]":
                        depth -= 1
                        if depth == 0:
                            eq_list_end = idx + 1
                            break

                if eq_list_end is None:
                    break

                block_end = eq_list_end
                continue
            break

        while block_end < len(content) and content[block_end] in " \t":
            block_end += 1
        if block_end < len(content) and content[block_end] == "\n":
            block_end += 1

        formatted = pprint.pformat(self._conv_layers, width=80, indent=4)
        replacement = f"CONV_LAYER_SPEC: List[dict] = {formatted}\n"

        new_content = content[:start] + replacement + content[block_end:]

        try:
            with open(self._classification_python_path, "w", encoding="utf-8") as handle:
                handle.write(new_content)
        except OSError as exc:
            print(f"Failed to update classifier_prototype.py: {exc}")

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
