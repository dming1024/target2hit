"""Resolve gene symbol → UniProt ID → PDB/AlphaFold structure."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Tuple
import httpx

logger = logging.getLogger(__name__)
UNIPROT_API = "https://rest.uniprot.org/uniprotkb"
PDB_SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2/query"
PDB_DOWNLOAD_URL = "https://files.rcsb.org/download"
ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction"


def resolve_uniprot(gene_symbol: str) -> str:
    """Resolve gene symbol to UniProt accession (human)."""
    params = {
        "query": f"gene:{gene_symbol} AND organism_id:9606 AND reviewed:true",
        "format": "json",
        "size": 1,
    }
    response = httpx.get(f"{UNIPROT_API}/search", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    if not results:
        raise ValueError(f"No UniProt entry found for gene: {gene_symbol}")
    return results[0]["primaryAccession"]


def search_pdb(uniprot_id: str, max_resolution: float = 3.0) -> Optional[dict]:
    """Search PDB for best experimental structure by resolution."""
    query = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                        "operator": "exact_match",
                        "value": uniprot_id,
                    },
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_entry_info.resolution_combined",
                        "operator": "less_or_equal",
                        "value": max_resolution,
                    },
                },
            ],
        },
        "return_type": "entry",
        "request_options": {
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}],
            "paginate": {"start": 0, "rows": 1},
        },
    }
    response = httpx.post(PDB_SEARCH_API, json=query, timeout=30)
    response.raise_for_status()
    if response.status_code == 204 or not response.text.strip():
        return None
    data = response.json()
    results = data.get("result_set", [])
    if not results:
        return None
    entry = results[0]
    return {
        "pdb_id": entry["identifier"],
        "resolution": entry.get("rcsb_entry_info", {}).get("resolution_combined"),
        "source": "pdb",
    }


def download_from_alphafold(uniprot_id: str) -> Path:
    """Download AlphaFold predicted structure."""
    response = httpx.get(f"{ALPHAFOLD_API}/{uniprot_id}", timeout=30)
    response.raise_for_status()
    data = response.json()
    pdb_url = data[0].get("pdbUrl") if isinstance(data, list) else data.get("pdbUrl")
    if not pdb_url:
        raise ValueError(f"No AlphaFold structure for {uniprot_id}")

    pdb_response = httpx.get(pdb_url, timeout=60)
    pdb_response.raise_for_status()
    output = Path(f"/tmp/{uniprot_id}_alphafold.pdb")
    output.write_text(pdb_response.text)
    return output


def download_structure(structure_info: Optional[dict], uniprot_id: str) -> Tuple[Path, str]:
    """Download structure, preferring PDB over AlphaFold."""
    if structure_info and structure_info["source"] == "pdb":
        pdb_id = structure_info["pdb_id"]
        url = f"{PDB_DOWNLOAD_URL}/{pdb_id}.pdb"
        response = httpx.get(url, timeout=60)
        response.raise_for_status()
        output = Path(f"/tmp/{pdb_id}.pdb")
        output.write_text(response.text)
        return output, "pdb"

    af_path = download_from_alphafold(uniprot_id)
    return af_path, "alphafold"
