"""Compound library loader (sample data, SDF, TSV/CSV)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Compound:
    compound_id: str
    smiles: str


class CompoundLibrary:
    """Loads and batches compounds."""

    def __init__(self, max_compounds: int = 100000):
        self.max_compounds = max_compounds
        self.compounds: List[Compound] = []

    def load_sample(self) -> None:
        """Load a built-in sample set for testing the pipeline."""
        self.compounds = [
            Compound("SAMPLE001", "CC(=O)OC1=CC=CC=C1C(=O)O"),
            Compound("SAMPLE002", "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"),
            Compound("SAMPLE003", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"),
            Compound("SAMPLE004", "C1=CC=C2C(=C1)C(=CN2)CC(=O)O"),
            Compound("SAMPLE005", "CC(=O)Nc1ccc(O)cc1"),
            Compound("SAMPLE006", "CN1CCC[C@H]1c2cccnc2"),
            Compound("SAMPLE007", "O=C(O)CCc1ccc(O)c(O)c1"),
            Compound("SAMPLE008", "Cc1ccc(C)c(O)c1"),
            Compound("SAMPLE009", "O=C(N1)C=NC1=O"),
            Compound("SAMPLE010", "CCN(CC)C(=O)c1cn(C)c2ccccc12"),
        ]
        logger.info(f"Loaded {len(self.compounds)} sample compounds")

    def load_from_smiles_file(self, path: str, id_col: int = 0, smiles_col: int = 1) -> None:
        """Load compounds from a TSV/CSV file."""
        import csv
        with open(path) as f:
            reader = csv.reader(f, delimiter="\t" if path.endswith(".tsv") else ",")
            next(reader, None)
            count = 0
            for row in reader:
                if count >= self.max_compounds:
                    break
                if len(row) > max(id_col, smiles_col):
                    self.compounds.append(Compound(
                        compound_id=row[id_col],
                        smiles=row[smiles_col],
                    ))
                    count += 1
        logger.info(f"Loaded {count} compounds from {path}")

    def get_batch(self, batch_size: int, offset: int = 0) -> List[Compound]:
        """Get a batch of compounds by offset."""
        return self.compounds[offset:offset + batch_size]

    def __len__(self) -> int:
        return len(self.compounds)
