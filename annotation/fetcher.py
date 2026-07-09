"""Fetch compound metadata from public databases."""
from __future__ import annotations
import logging
from typing import Dict
import httpx

logger = logging.getLogger(__name__)


def fetch_pubchem(smiles: str) -> Dict[str, str]:
    """Fetch PubChem CID by SMILES."""
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles}/cids/JSON"
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        cid = str(data["IdentifierList"]["CID"][0])
        return {"pubchem_cid": cid}
    except Exception as e:
        logger.debug(f"PubChem lookup failed for {smiles[:30]}: {e}")
        return {}


def fetch_chembl(smiles: str) -> Dict[str, str]:
    """Fetch ChEMBL info by SMILES."""
    try:
        response = httpx.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            params={"smiles": smiles, "limit": 1},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        molecules = data.get("molecules", [])
        if molecules:
            mol = molecules[0]
            return {
                "chembl_id": mol.get("molecule_chembl_id", ""),
                "pref_name": mol.get("pref_name", ""),
                "max_phase": str(mol.get("max_phase", "")),
            }
        return {}
    except Exception as e:
        logger.debug(f"ChEMBL lookup failed for {smiles[:30]}: {e}")
        return {}
