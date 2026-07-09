"""Tests for AI screening encoders."""
import numpy as np
import pytest
from screening.protein_encoder import ProteinEncoder
from screening.ligand_encoder import LigandEncoder
from screening.compound_library import CompoundLibrary, Compound


class TestCompoundLibrary:
    def test_load_sample(self):
        lib = CompoundLibrary()
        lib.load_sample()
        assert len(lib.compounds) > 0
        c = lib.compounds[0]
        assert isinstance(c, Compound)
        assert c.compound_id
        assert c.smiles

    def test_get_batch(self):
        lib = CompoundLibrary()
        lib.load_sample()
        batch = lib.get_batch(10, offset=0)
        assert len(batch) <= 10
        batch2 = lib.get_batch(10, offset=10)
        if len(batch2) > 0:
            assert batch[0].compound_id != batch2[0].compound_id


class TestProteinEncoder:
    def test_device_auto_detect(self):
        encoder = ProteinEncoder()
        assert encoder.device in ("cpu", "cuda")

    @pytest.mark.skip(reason="Requires ESM2 model download (~150MB) from HuggingFace")
    def test_encode_sequence(self):
        encoder = ProteinEncoder()
        embedding = encoder.encode("MPSK")
        assert embedding.shape == (640,)
        assert isinstance(embedding, np.ndarray)


class TestLigandEncoder:
    @pytest.mark.skip(reason="Requires ChemBERTa model download (~300MB) from HuggingFace")
    def test_encode_smiles(self):
        encoder = LigandEncoder()
        embedding = encoder.encode("CC(=O)OC1=CC=CC=C1C(=O)O")
        assert embedding.shape == (600,)

    @pytest.mark.skip(reason="Requires ChemBERTa model download (~300MB) from HuggingFace")
    def test_encode_batch(self):
        encoder = LigandEncoder()
        smiles_list = [
            "CC(=O)OC1=CC=CC=C1C(=O)O",
            "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
            "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        ]
        embeddings = encoder.encode_batch(smiles_list, batch_size=2)
        assert embeddings.shape == (3, 600)
