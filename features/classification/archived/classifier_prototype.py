"""Prototype deep-learning classifier pipeline built with PyTorch.

This module wires a configurable convolutional network to a training loop
complete with synthetic data fallbacks. The convolutional architecture is
populated from the configuration list defined below, which stays in sync with
the Qt UI via ``config_manager``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np
import torch
from torch import Tensor
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONV_LAYER_SPEC: List[dict] = [   {'inChannels': 3, 'kernelSize': 3, 'outChannels': 32, 'padding': 0},
    {'inChannels': 32, 'kernelSize': 3, 'outChannels': 64, 'padding': 1},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2},
    {'inChannels': 64, 'kernelSize': 5, 'outChannels': 128, 'padding': 2}]
+ [
    {"inChannels": 64, "outChannels": 128, "kernelSize": 5, "padding": 2}
    for _ in range(12)
]


@dataclass
class TrainingConfig:
    dataset_path: Optional[Path] = None
    epochs: int = 30
    batch_size: int = 32
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    train_split: float = 0.8
    num_workers: int = 0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    num_classes: int = 2
    input_channels: int = 3
    input_timepoints: int = 256


def load_conv_layer_config() -> List[dict]:
    """Return a deep copy of the current convolutional specification."""

    return [layer.copy() for layer in CONV_LAYER_SPEC]


class EEGConvNet(nn.Module):
    """Simplified CNN that applies the configured conv blocks in sequence."""

    def __init__(self, conv_spec: Iterable[dict], input_channels: int, num_classes: int):
        super().__init__()
        layers: List[nn.Module] = []
        next_in = input_channels
        for spec in conv_spec:
            out_channels = int(spec.get("outChannels", next_in))
            kernel_size = int(spec.get("kernelSize", 3))
            padding = int(spec.get("padding", 0))
            stride = int(spec.get("stride", 1))
            layers.append(
                nn.Conv2d(
                    in_channels=next_in,
                    out_channels=out_channels,
                    kernel_size=kernel_size,
                    padding=padding,
                    stride=stride,
                )
            )
            layers.append(nn.BatchNorm2d(out_channels))
            layers.append(nn.ReLU(inplace=True))
            if spec.get("pool"):
                pool_kernel = int(spec.get("poolKernel", 2))
                layers.append(nn.MaxPool2d(kernel_size=pool_kernel))
            dropout_prob = float(spec.get("dropout", 0.0))
            if dropout_prob > 0:
                layers.append(nn.Dropout2d(p=dropout_prob))
            next_in = out_channels

        self.feature_extractor = nn.Sequential(*layers)
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(next_in, max(32, next_in // 2)),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.3),
            nn.Linear(max(32, next_in // 2), num_classes),
        )

    def forward(self, x: Tensor) -> Tensor:
        feats = self.feature_extractor(x)
        return self.classifier(feats)


class NpyWindowDataset(Dataset):
    """Dataset wrapper for pre-extracted tensor windows.

    If ``root`` is ``None`` or empty, synthetic samples are generated so the
    training loop can still execute end-to-end.
    """

    def __init__(self, root: Optional[Path], length: int, channels: int, timepoints: int, num_classes: int):
        self.root = root
        self.length = length
        self.channels = channels
        self.timepoints = timepoints
        self.num_classes = num_classes

        if self.root and self.root.exists():
            self.files = sorted(self.root.glob("*.pt")) + sorted(self.root.glob("*.pth"))
            self.files += sorted(self.root.glob("*.npy"))
            if not self.files:
                raise FileNotFoundError(f"No tensor files found in {self.root}")
            self.length = len(self.files)
        else:
            self.files: List[Path] = []

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: int) -> Tuple[Tensor, int]:
        if self.files:
            path = self.files[index]
            if path.suffix == ".npy":
                array = torch.from_numpy(np.load(path))  # type: ignore[arg-type]
            else:
                array = torch.load(path)
            tensor = array.float()
        else:
            torch.manual_seed(index)
            tensor = torch.randn(self.channels, 1, self.timepoints)

        label = index % self.num_classes
        return tensor, label


def build_dataloaders(cfg: TrainingConfig) -> Tuple[DataLoader, DataLoader]:
    dataset = NpyWindowDataset(
        root=cfg.dataset_path,
        length=1000,
        channels=cfg.input_channels,
        timepoints=cfg.input_timepoints,
        num_classes=cfg.num_classes,
    )

    train_len = int(len(dataset) * cfg.train_split)
    val_len = len(dataset) - train_len
    train_ds, val_ds = random_split(dataset, [train_len, val_len])

    train_loader = DataLoader(
        train_ds,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
    )
    return train_loader, val_loader


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: str,
) -> float:
    model.train()
    running_loss = 0.0
    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    return running_loss / max(1, len(loader))


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: str) -> Tuple[float, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device)
        logits = model(inputs)
        loss = criterion(logits, targets)
        total_loss += loss.item()
        preds = logits.argmax(dim=1)
        correct += (preds == targets).sum().item()
        total += targets.numel()
    avg_loss = total_loss / max(1, len(loader))
    accuracy = correct / max(1, total)
    return avg_loss, accuracy


def run_training(cfg: TrainingConfig) -> None:
    conv_spec = load_conv_layer_config()
    model = EEGConvNet(conv_spec, input_channels=cfg.input_channels, num_classes=cfg.num_classes)
    model.to(cfg.device)

    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)

    train_loader, val_loader = build_dataloaders(cfg)

    best_acc = 0.0
    best_state = None
    for epoch in range(1, cfg.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, cfg.device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, cfg.device)
        print(
            "Epoch {}/{:02d} | train_loss={:.4f} | val_loss={:.4f} | val_acc={:.3f}".format(
                epoch,
                cfg.epochs,
                train_loss,
                val_loss,
                val_acc,
            )
        )
        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
            }

    if best_state:
        output_dir = PROJECT_ROOT / "artifacts"
        output_dir.mkdir(parents=True, exist_ok=True)
        torch.save(best_state, output_dir / "classifier_prototype_best.pth")
        print(f"Best checkpoint saved with val_acc={best_acc:.3f}")


def parse_args() -> TrainingConfig:
    parser = argparse.ArgumentParser(description="Prototype deep-learning classifier trainer")
    parser.add_argument("--dataset", type=str, default=None, help="Directory containing .pt/.pth/.npy tensors")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--train-split", type=float, default=0.8)
    parser.add_argument("--num-classes", type=int, default=2)
    parser.add_argument("--channels", type=int, default=3)
    parser.add_argument("--timepoints", type=int, default=256)
    args = parser.parse_args()

    dataset_path = Path(args.dataset) if args.dataset else None
    return TrainingConfig(
        dataset_path=dataset_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        train_split=args.train_split,
        num_classes=args.num_classes,
        input_channels=args.channels,
        input_timepoints=args.timepoints,
    )


def main() -> None:
    cfg = parse_args()
    run_training(cfg)


if __name__ == "__main__":
    main()
