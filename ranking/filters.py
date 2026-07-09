"""Molecular property filters: drug-likeness, PAINS, SA, novelty."""
from __future__ import annotations
from rdkit import Chem
from rdkit.Chem import Descriptors, QED


def compute_drug_likeness(smiles: str) -> float:
    """Compute QED (Quantitative Estimate of Drug-likeness). Range: 0-1."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0.0
    return QED.qed(mol)


def check_pains(smiles: str) -> bool:
    """Check if compound contains PAINS substructures."""
    from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return True
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
    catalog = FilterCatalog(params)
    entry = catalog.GetFirstMatch(mol)
    return entry is not None


def compute_sa_score(smiles: str) -> float:
    """Compute Synthetic Accessibility score. Range: typically 1-10."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 10.0
    try:
        from rdkit.Contrib.SA_Score import sascorer
        return sascorer.calculateScore(mol)
    except (ImportError, AttributeError):
        # Fallback: rough estimate based on molecular weight
        mw = Descriptors.MolWt(mol)
        return max(1.0, min(10.0, mw / 50.0))


def compute_novelty(smiles: str, known_smiles: list[str] | None = None) -> float:
    """Compute novelty as 1 - max Tanimoto similarity to known drugs."""
    if not known_smiles:
        return 1.0
    from rdkit.Chem import rdMolDescriptors
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0.0
    fp = Chem.RDKFingerprint(mol)
    max_sim = 0.0
    for known in known_smiles:
        known_mol = Chem.MolFromSmiles(known)
        if known_mol is None:
            continue
        known_fp = Chem.RDKFingerprint(known_mol)
        sim = rdMolDescriptors.TanimotoSimilarity(fp, known_fp)
        max_sim = max(max_sim, sim)
    return 1.0 - max_sim
