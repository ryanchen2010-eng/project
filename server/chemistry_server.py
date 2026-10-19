"""Local RDKit service for the small-molecule Builder and Reaction Lab.

Run with ``.venv/bin/python server/chemistry_server.py``. Vite proxies
``/api/chemistry`` to this loopback-only process during local development.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors

if __package__:
    from .reaction_condition_guidance import guidance as guided_condition_metadata
else:
    from reaction_condition_guidance import guidance as guided_condition_metadata

if __package__:
    from .pubchem_service import PubChemError, get_pubchem_depiction, get_pubchem_smiles, get_pubchem_structure, search_pubchem
    from .reaction_diagrams import build_reaction_diagram, mapped_product_molecule
    from .reaction_engine import generate_pair, reagent_role
    from .reaction_reasoning import explain_pathway, compare_pathways
    from .reaction_conditions import assess_conditions, REVIEWED
    from .reaction_mechanisms import build_mechanism
    from .reaction_information import reaction_information
    from .functional_groups import inspect_structure
    from . import ester_rules, molecular_graph, hydration_rule, epoxidation_rule, dihydroxylation_rule, addition_contract, alkyne_partial_hydrogenation_rule, alkyne_complete_hydrogenation_rule, alkyne_halogenation_rule, alkyne_hydrohalogenation_rule, alcohol_dehydration_rule, alcohol_substitution_rule, primary_alcohol_oxidation_rule, secondary_alcohol_oxidation_rule
    from .stereochemistry import stereo_scope_issue
else:  # Also support the documented ``python server/chemistry_server.py`` command.
    from pubchem_service import PubChemError, get_pubchem_depiction, get_pubchem_smiles, get_pubchem_structure, search_pubchem
    from reaction_diagrams import build_reaction_diagram, mapped_product_molecule
    from reaction_engine import generate_pair, reagent_role
    from reaction_reasoning import explain_pathway, compare_pathways
    from reaction_conditions import assess_conditions, REVIEWED
    from reaction_mechanisms import build_mechanism
    from reaction_information import reaction_information
    from functional_groups import inspect_structure
    import ester_rules, molecular_graph, hydration_rule, epoxidation_rule, dihydroxylation_rule, addition_contract, alkyne_partial_hydrogenation_rule, alkyne_complete_hydrogenation_rule, alkyne_halogenation_rule, alkyne_hydrohalogenation_rule, alcohol_dehydration_rule, alcohol_substitution_rule, primary_alcohol_oxidation_rule, secondary_alcohol_oxidation_rule
    from stereochemistry import stereo_scope_issue


MAX_BODY_BYTES = 200_000
MAX_ATOMS = 80
ALLOWED_ELEMENTS = {"H", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Br", "I"}
BUILDER_3D_ELEMENTS = {"H", "B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Ge", "As", "Se", "Br", "Sb", "Te", "I"}
ELEMENT_NAMES = {"C": "Carbon", "N": "Nitrogen", "O": "Oxygen", "H": "Hydrogen"}

# Example identity/display data. Eligibility is decided by reaction_engine's
# structural rules, never by membership in this collection.
# The source links explain the reaction classes and required conditions.
REACTANTS = {
    "ethene": {"name": "Ethene", "smiles": "C=C", "aliases": ["ethylene"]},
    "hydrogen": {"name": "Hydrogen", "smiles": "[H][H]", "aliases": ["H2"]},
    "bromine": {"name": "Bromine", "smiles": "BrBr", "aliases": ["Br2"]},
    "chlorine": {"name": "Chlorine", "smiles": "ClCl", "aliases": ["Cl2"]},
    "hydrogen-chloride": {"name": "Hydrogen chloride", "smiles": "Cl", "aliases": ["HCl"]},
    "hydrogen-bromide": {"name": "Hydrogen bromide", "smiles": "Br", "aliases": ["HBr"]},
    "hydrogen-iodide": {"name": "Hydrogen iodide", "smiles": "I", "aliases": ["HI"]},
    "water": {"name": "Water", "smiles": "O", "aliases": ["H2O"]},
    "peracetic-acid": {"name": "Peracetic acid", "smiles": "CC(=O)OO", "aliases": ["peroxyacetic acid", "peroxyethanoic acid"]},
    "sulfuric-acid": {"name": "Sulfuric acid", "smiles": "OS(=O)(=O)O", "aliases": ["H2SO4", "sulphuric acid"]},
    "hydrogen-peroxide": {"name": "Hydrogen peroxide", "smiles": "OO", "aliases": ["H2O2"]},
    "benzoyl-peroxide": {"name": "Benzoyl peroxide", "smiles": "O=C(OOC(=O)c1ccccc1)c1ccccc1", "aliases": ["dibenzoyl peroxide"]},
    "propyne": {"name": "Propyne", "smiles": "CC#C", "aliases": ["methylacetylene"]},
    "ethanol": {"name": "Ethanol", "smiles": "CCO", "aliases": ["ethyl alcohol"]},
    "dimethyl-ether": {"name": "Dimethyl ether", "smiles": "COC", "aliases": ["methoxymethane"]},
    "ethanoic-acid": {"name": "Ethanoic acid", "smiles": "CC(=O)O", "aliases": ["acetic acid"]},
    "bromomethane": {"name": "Bromomethane", "smiles": "CBr", "aliases": ["methyl bromide"]},
    "chloromethane": {"name": "Chloromethane", "smiles": "CCl", "aliases": ["methyl chloride"]},
    "bromoethane": {"name": "Bromoethane", "smiles": "CCBr", "aliases": ["ethyl bromide"]},
    "2-bromopropane": {"name": "2-Bromopropane", "smiles": "CC(C)Br", "aliases": ["isopropyl bromide"]},
    "tert-butyl-chloride": {"name": "2-Chloro-2-methylpropane", "smiles": "CC(C)(C)Cl", "aliases": ["tert-butyl chloride"]},
    "hydroxide": {"name": "Hydroxide ion", "smiles": "[OH-]", "formula": "OH⁻", "aliases": ["hydroxide", "OH-", "HO-"]},
    "sodium-hypochlorite": {"name": "Sodium hypochlorite", "smiles": "[Na+].[O-]Cl", "formula": "NaClO", "aliases": ["sodium oxychloride", "NaClO"]},
}

# Explorer and Reaction Lab use the same source of compound names, structures,
# formulas, and PubChem identities. Reagents specific to Reaction Lab stay above.
SHARED_MOLECULES = json.loads((Path(__file__).resolve().parents[1] / "src" / "shared-molecules.json").read_text(encoding="utf-8"))
FORMULA_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
REACTANTS.update({item["id"]: {"name": item["name"], "smiles": item["smiles"],
                               "formula": item["formula"].translate(FORMULA_SUBSCRIPTS), "aliases": item["aliases"]}
                  for item in SHARED_MOLECULES})
REACTIONS = {
    "hydrogenation": {
        "name": "Hydrogenation", "reactants": ("ethene", "hydrogen"),
        "family": "Addition", "mechanism": "Hydrogenation", "profile": {"catalyst": "metal"},
        "productName": "Ethane", "productSmiles": "CC", "byproducts": [],
        "conditions": "Requires a metal catalyst such as palladium or platinum.",
        "explanation": "The carbon–carbon double bond becomes a single bond as two hydrogen atoms add.",
        "sourceUrl": "https://openstax.org/books/organic-chemistry/pages/8-summary",
    },
    "bromination": {
        "name": "Bromine addition", "reactants": ("ethene", "bromine"),
        "family": "Addition", "mechanism": "Bromination", "profile": {"solvent": "dry"},
        "productName": "1,2-Dibromoethane", "productSmiles": "BrCCBr", "byproducts": [],
        "conditions": "Shown for bromine addition to ethene without water as a competing reactant.",
        "explanation": "The double bond becomes a single bond and one bromine bonds to each carbon.",
        "sourceUrl": "https://openstax.org/books/organic-chemistry/pages/8-2-halogenation-of-alkenes-addition-of-x2",
    },
    "hydration": {
        "name": "Alkene hydration", "reactants": ("ethene", "water"),
        "family": "Addition", "mechanism": "Hydration", "profile": {"catalyst": "acid"},
        "productName": "Ethanol", "productSmiles": "CCO", "byproducts": [],
        "conditions": "Requires acid-catalyzed hydration; simply mixing ethene and water is not enough.",
        "explanation": "Hydrogen and an OH group add across the carbon–carbon double bond.",
        "sourceUrl": "https://openstax.org/books/organic-chemistry/pages/8-summary",
    },
    "esterification": {
        "name": "Fischer esterification", "reactants": ("ethanoic-acid", "ethanol"),
        "family": "Condensation", "mechanism": "Esterification", "profile": {"catalyst": "acid"},
        "productName": "Ethyl ethanoate", "productSmiles": "CC(=O)OCC",
        "byproducts": [{"name": "Water", "smiles": "O"}],
        "conditions": "Requires an acid catalyst. This reaction is reversible and depends on conditions.",
        "explanation": "The acid and alcohol form an ester and water; the display shows one possible equilibrium direction.",
        "sourceUrl": "https://openstax.org/books/organic-chemistry/pages/21-3-reactions-of-carboxylic-acids",
    },
    "ester-hydrolysis": {
        "name": "Acid-catalyzed ester hydrolysis", "reactants": ("ethyl-ethanoate", "water"),
        "family": "Hydrolysis", "mechanism": "Ester hydrolysis", "profile": {"solvent": "aqueous-protic", "catalyst": "acid"},
        "productName": "Ethanoic acid", "productSmiles": "CC(=O)O",
        "byproducts": [{"name": "Ethanol", "smiles": "CCO"}],
        "conditions": "Acid-catalyzed hydrolysis in water; this is the reversible counterpart of Fischer esterification.",
        "explanation": "Water helps split the ester linkage. The displayed net products are ethanoic acid and ethanol; the acid catalyst is not consumed.",
        "sourceUrl": "https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters",
    },
    "oxidation-2-propanol": {
        "name": "Secondary alcohol oxidation", "reactants": ("2-propanol", "sodium-hypochlorite"),
        "family": "Oxidation", "mechanism": "Alcohol oxidation", "profile": {"solvent": "aqueous-protic"},
        "productName": "Acetone", "productSmiles": "CC(C)=O",
        "byproducts": [{"name": "Sodium chloride", "smiles": "[Na+].[Cl-]", "formula": "NaCl"}, {"name": "Water", "smiles": "O"}],
        "conditions": "A simplified net equation for hypochlorite oxidation in an aqueous medium. Actual mixtures and side reactions are not modeled; do not treat this as a procedure or mix household chemicals.",
        "explanation": "The secondary alcohol carbon loses hydrogen as its C–O bond becomes a carbonyl C=O bond. Hypochlorite is reduced to chloride in this net equation.",
        "sourceUrl": "https://pubs.acs.org/doi/abs/10.1021/ed059p862",
    },
    "reduction-acetone": {
        "name": "Ketone hydrogenation", "reactants": ("acetone", "hydrogen"),
        "family": "Reduction", "mechanism": "Carbonyl hydrogenation", "profile": {"catalyst": "metal"},
        "productName": "2-Propanol", "productSmiles": "CC(C)O", "byproducts": [],
        "conditions": "Requires a suitable metal catalyst and hydrogenation conditions. Ketones may need more demanding conditions than alkenes; this lab does not model pressure or yield.",
        "explanation": "Hydrogen adds across the ketone C=O bond, converting acetone into the secondary alcohol 2-propanol.",
        "sourceUrl": "https://iris.cnr.it/handle/20.500.14243/209294",
    },
    "sn2-bromomethane": {
        "name": "SN2 substitution", "reactants": ("bromomethane", "hydroxide"),
        "family": "Substitution", "mechanism": "SN2", "profile": {"solvent": "polar-aprotic"},
        "productName": "Methanol", "productSmiles": "CO", "productEquationFormula": "CH3OH",
        "byproducts": [{"name": "Bromide ion", "smiles": "[Br-]", "formula": "Br⁻"}],
        "conditions": "Shown for an unhindered methyl halide and hydroxide; solvent affects the reaction rate.",
        "explanation": "Hydroxide forms a C–O bond as bromide leaves in one concerted SN2 step. Methyl carbon is not chiral, so there is no inversion to display here.",
        "sourceUrl": "https://openstax.org/books/organic-chemistry/pages/11-2-the-sn2-reaction",
    },
    "sn2-chloromethane": {
        "name": "SN2 substitution", "reactants": ("chloromethane", "hydroxide"),
        "family": "Substitution", "mechanism": "SN2", "profile": {"solvent": "polar-aprotic"},
        "productName": "Methanol", "productSmiles": "CO", "productEquationFormula": "CH3OH",
        "byproducts": [{"name": "Chloride ion", "smiles": "[Cl-]", "formula": "Cl⁻"}],
        "conditions": "Shown for an unhindered methyl halide and hydroxide; substrate, leaving group, and solvent affect the rate.",
        "explanation": "Hydroxide forms a C–O bond as chloride leaves in one concerted SN2 step. This example changes the leaving group, not the organic product.",
        "sourceUrl": "https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction",
    },
}

# Profiles compare illustrative conditions; they are not kinetic predictions.
# Non-aligned pathways remain visible because mechanisms may compete.
CONDITION_VALUES = {
    "solvent": {"", "polar-aprotic", "aqueous-protic", "ethanolic-protic", "dry"},
    "temperature": {"", "ambient", "heated"},
    "catalyst": {"", "none", "acid", "metal", "lindlar", "osmium", "radical"},
    "oxidationStage": {"", "first", "further"},
    "additionStage": {"", "one", "two"},
    "polymerUnits": {"", "2", "4", "6"},
    "workup": {"", "aqueous-release"},
}

PRODUCT_NAMES = {
    "CCO": "Ethanol",
    "CCC": "Propane",
    "CCCC": "Butane",
    "CCCO": "1-Propanol",
    "CC(C)O": "2-Propanol",
    "CC(C)(C)O": "2-Methyl-2-propanol",
    "CC(Br)CBr": "1,2-Dibromopropane",
    "CCC(Br)CBr": "1,2-Dibromobutane",
    "C=C": "Ethene",
    "C=CC": "Propene",
    "C=C(C)C": "2-Methylpropene",
}


class ChemistryError(ValueError):
    """A requested structure or curated reaction is outside the current scope."""


def _molecule(smiles: str) -> Chem.Mol:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise RuntimeError(f"Invalid curated structure: {smiles}")
    return molecule


def _formula(smiles: str) -> str:
    return rdMolDescriptors.CalcMolFormula(_molecule(smiles))


def _element_counts(smiles: str) -> Counter[str]:
    return Counter(atom.GetSymbol() for atom in Chem.AddHs(_molecule(smiles)).GetAtoms())


def _formal_charge(smiles: str) -> int:
    return sum(atom.GetFormalCharge() for atom in _molecule(smiles).GetAtoms())


# Catalog pairs are examples only. All eligibility/products come from generate_pair.
CATALOG_PAIRS = [
    *[tuple(item["reactants"]) for item in REACTIONS.values()],
    ("bromoethane", "hydroxide"), ("2-bromopropane", "hydroxide"),
    ("tert-butyl-chloride", "hydroxide"), ("tert-butyl-chloride", "water"),
    ("propene", "hydrogen"), ("propene", "bromine"),
    ("ethene", "peracetic-acid"),
]
ALKALI_COUNTERIONS = {"Li", "Na", "K", "Rb", "Cs"}


def _reactions_for_pair(first, second, catalog, conditions=None):
    # Exact identity data below supplies names / stable example IDs ONLY.
    # It cannot add eligibility or change a graph-generated product.
    names = {Chem.MolToSmiles(_molecule(item["smiles"]), canonical=True): item["name"]
             for item in catalog.values()}
    names.update({Chem.MolToSmiles(_molecule(smiles), canonical=True): name
                  for smiles, name in PRODUCT_NAMES.items()})
    for example in REACTIONS.values():
        names[Chem.MolToSmiles(_molecule(example["productSmiles"]), canonical=True)] = example["productName"]
    generated, notes = generate_pair(first, second, catalog, names, conditions=conditions)
    result = {}
    for identifier, reaction in generated.items():
        same_options = [r for r in generated.values()
                        if r["mechanism"] == reaction["mechanism"] and r["reactants"] == reaction["reactants"]]
        for example_id, example in REACTIONS.items():
            if (len(same_options) == 1 and sorted(example["reactants"]) == sorted(reaction["reactants"])
                    and example["mechanism"] == reaction["mechanism"]):
                identifier = example_id
                if ("productEquationFormula" in example and
                        Chem.MolToSmiles(_molecule(example["productSmiles"]), canonical=True) == reaction["productSmiles"]):
                    reaction["productEquationFormula"] = example["productEquationFormula"]
                break
        for product in reaction["byproducts"]:
            for example in REACTIONS.values():
                for display in example["byproducts"]:
                    if "formula" in display and Chem.MolToSmiles(_molecule(display["smiles"]), canonical=True) == product["smiles"]:
                        product["formula"] = display["formula"]
        reaction["site"]["siteId"] = identifier
        result[identifier] = reaction
    return result, notes


def _all_reactions(custom_reactants=None):
    catalog = {**REACTANTS, **(custom_reactants or {})}
    pairs = list(CATALOG_PAIRS)
    if custom_reactants:
        pairs.extend((first, second) for first in custom_reactants for second in catalog if first != second)
    result = {}
    for first, second in pairs:
        result.update(_reactions_for_pair(first, second, catalog)[0])
    return result


def _hydroxide_from_salt(molecule: Chem.Mol) -> str | None:
    """Recognize a single alkali cation plus hydroxide for an ionic equation."""
    fragments = Chem.GetMolFrags(molecule, asMols=True)
    if len(fragments) != 2:
        return None
    hydroxides = [fragment for fragment in fragments if Chem.MolToSmiles(fragment, canonical=True) == "[OH-]"]
    cations = [fragment for fragment in fragments if fragment.GetNumAtoms() == 1
               and fragment.GetAtomWithIdx(0).GetSymbol() in ALKALI_COUNTERIONS
               and fragment.GetAtomWithIdx(0).GetFormalCharge() == 1]
    return cations[0].GetAtomWithIdx(0).GetSymbol() if len(hydroxides) == len(cations) == 1 else None


def _resolve_reactants(reactant_a: str | dict[str, str], reactant_b: str | dict[str, str]) -> tuple[tuple[str, str], dict[str, dict[str, object]], list[str]]:
    """Keep reviewed IDs stable and validate searched or drawn structures."""
    custom = {}
    ids = []
    interpretation_notes = []
    for slot, reference in enumerate((reactant_a, reactant_b)):
        if isinstance(reference, str) and reference in REACTANTS:
            if reference == "sodium-hydroxide":
                ids.append("hydroxide")
                interpretation_notes.append(f"Molecule {slot + 1}: sodium hydroxide supplies OH⁻; Na⁺ is omitted from the simplified ionic equation.")
                continue
            ids.append(reference)
            continue
        if not isinstance(reference, dict) or not isinstance(reference.get("smiles"), str):
            raise ChemistryError("Choose a listed molecule or send a valid Builder drawing.")
        smiles = reference["smiles"]
        if not smiles or len(smiles) > 1024:
            raise ChemistryError("The Builder structure is empty or too large.")
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None or not molecule.GetNumAtoms() or molecule.GetNumAtoms() > MAX_ATOMS:
            raise ChemistryError("The Builder structure is invalid or too large.")
        if reagent_role(molecule) == "hydrogen-peroxide":
            partner = (reactant_a, reactant_b)[1 - slot]
            partner_smiles = (REACTANTS[partner]["smiles"] if isinstance(partner,str) and partner in REACTANTS else partner.get("smiles") if isinstance(partner,dict) else None)
            partner_mol = Chem.MolFromSmiles(partner_smiles) if isinstance(partner_smiles,str) and 0 < len(partner_smiles) <= 1024 else None
            if partner_mol is not None and molecular_graph.find_alkenes(partner_mol):
                issue = dihydroxylation_rule.input_reagent_issue(smiles)
                if issue: raise ChemistryError(issue)
        if epoxidation_rule.peroxyacid_sites(molecule):
            partner = (reactant_a, reactant_b)[1 - slot]
            partner_smiles = (REACTANTS[partner]["smiles"] if isinstance(partner, str) and partner in REACTANTS else
                              partner.get("smiles") if isinstance(partner, dict) else None)
            partner_mol = (Chem.MolFromSmiles(partner_smiles)
                           if isinstance(partner_smiles, str) and 0 < len(partner_smiles) <= 1024 else None)
            if partner_mol is not None and molecular_graph.find_alkenes(partner_mol):
                peracid_issue = epoxidation_rule.input_stereo_issue(smiles, molecule)
                if peracid_issue:
                    raise ChemistryError(peracid_issue)
        # Ordinary SMILES canonicalization drops CX enhanced stereo groups.
        # Reject these ester inputs BEFORE that boundary, never silently erase
        # relative/racemic or unsupported non-tetrahedral configurations.
        if molecular_graph.find_esters(molecule):
            stereo_issue = ester_rules.stereo_scope_issue(molecule)
            if stereo_issue:
                raise ChemistryError(stereo_issue)
        elif molecular_graph.find_alkenes(molecule):
            # This guard does not approve any other pathway. Nonstandard CX
            # stereo must not disappear before a site's policy can inspect it.
            stereo_issue = stereo_scope_issue(molecule, "the current alkene rules")
            if stereo_issue:
                raise ChemistryError(stereo_issue)
        elif molecular_graph.find_aldehydes(molecule) or molecular_graph.find_ketones(molecule):
            partner = (reactant_a, reactant_b)[1 - slot]
            partner_smiles = (REACTANTS[partner]["smiles"] if isinstance(partner, str) and partner in REACTANTS else
                              partner.get("smiles") if isinstance(partner, dict) else None)
            partner_mol = (Chem.MolFromSmiles(partner_smiles)
                           if isinstance(partner_smiles, str) and 0 < len(partner_smiles) <= 1024 else None)
            if partner_mol is not None and reagent_role(partner_mol) == "hydrogen":
                # Fail closed before ordinary SMILES can erase enhanced stereo.
                # This branch is specific to the new carbonyl/H2 consumer.
                stereo_issue = stereo_scope_issue(molecule, "carbonyl hydrogenation")
                if stereo_issue:
                    raise ChemistryError(stereo_issue)
        if molecular_graph.find_alcohols(molecule):
            partner = (reactant_a, reactant_b)[1 - slot]
            partner_smiles = (REACTANTS[partner]["smiles"] if isinstance(partner, str) and partner in REACTANTS else
                              partner.get("smiles") if isinstance(partner, dict) else None)
            partner_mol = (Chem.MolFromSmiles(partner_smiles)
                           if isinstance(partner_smiles, str) and 0 < len(partner_smiles) <= 1024 else None)
            if partner_mol is not None and reagent_role(partner_mol) == "hypochlorite":
                stereo_issue = stereo_scope_issue(molecule, "alcohol oxidation")
                if stereo_issue:
                    raise ChemistryError(stereo_issue)
                if primary_alcohol_oxidation_rule.sites(molecule):
                    stereo_issue = primary_alcohol_oxidation_rule.input_stereo_issue(smiles, molecule)
                    if stereo_issue: raise ChemistryError(stereo_issue)
                if secondary_alcohol_oxidation_rule.sites(molecule):
                    stereo_issue = secondary_alcohol_oxidation_rule.input_stereo_issue(smiles,molecule)
                    if stereo_issue: raise ChemistryError(stereo_issue)
            if partner_mol is not None and reagent_role(partner_mol) == "sulfuric-acid":
                stereo_issue = alcohol_dehydration_rule.input_stereo_issue(smiles, molecule)
                if stereo_issue: raise ChemistryError(stereo_issue)
            if partner_mol is not None and reagent_role(partner_mol) == "hydrogen-halide":
                stereo_issue = alcohol_substitution_rule.input_stereo_issue(smiles, molecule)
                if stereo_issue: raise ChemistryError(stereo_issue)
        if molecular_graph.find_alkyl_halides(molecule):
            partner = (reactant_a, reactant_b)[1 - slot]
            partner_smiles = (REACTANTS[partner]["smiles"] if isinstance(partner, str) and partner in REACTANTS else
                              partner.get("smiles") if isinstance(partner, dict) else None)
            partner_mol = (Chem.MolFromSmiles(partner_smiles)
                           if isinstance(partner_smiles, str) and 0 < len(partner_smiles) <= 1024 else None)
            if partner_mol is not None and (reagent_role(partner_mol) == "hydroxide" or _hydroxide_from_salt(partner_mol)):
                stereo_issue = stereo_scope_issue(molecule, "hydroxide SN2 substitution")
                if stereo_issue:
                    raise ChemistryError(stereo_issue)
            elif partner_mol is not None and reagent_role(partner_mol) == "water":
                stereo_issue = stereo_scope_issue(molecule, "water SN1 solvolysis")
                if stereo_issue:
                    raise ChemistryError(stereo_issue)
        if len(Chem.GetMolFrags(molecule)) != 1:
            counterion = _hydroxide_from_salt(molecule)
            if counterion:
                ids.append("hydroxide")
                interpretation_notes.append(f"Molecule {slot + 1}: this alkali-metal hydroxide supplies OH⁻; {counterion}⁺ is omitted from the simplified ionic equation.")
                continue
            if reagent_role(molecule) != "hypochlorite":
                raise ChemistryError("This multi-part compound is outside the current reaction rules.")
        hydration_stereo_issue = hydration_rule.input_stereo_issue(smiles, molecule)
        partial_alkyne_stereo_issue = (alkyne_partial_hydrogenation_rule.input_stereo_issue(smiles, molecule)
                                      if molecular_graph.find_alkynes(molecule) else None)
        complete_alkyne_stereo_issue = (alkyne_complete_hydrogenation_rule.input_stereo_issue(smiles, molecule)
                                       if molecular_graph.find_alkynes(molecule) else None)
        halogen_alkyne_stereo_issue = (alkyne_halogenation_rule.input_stereo_issue(smiles, molecule)
                                      if molecular_graph.find_alkynes(molecule) else None)
        hx_alkyne_stereo_issue = (alkyne_hydrohalogenation_rule.input_stereo_issue(smiles, molecule)
                                 if molecular_graph.find_alkynes(molecule) else None)
        canonical = Chem.MolToSmiles(molecule, canonical=True)
        reviewed_id = next(
            (key for key, item in REACTANTS.items()
             if Chem.MolToSmiles(_molecule(item["smiles"]), canonical=True) == canonical),
            None,
        )
        if reviewed_id:
            if partial_alkyne_stereo_issue:
                custom[reviewed_id] = {**REACTANTS[reviewed_id], "alkynePartialStereoIssue": partial_alkyne_stereo_issue}
            if hydration_stereo_issue:
                # Preserve only a hydration-specific input caveat when the
                # canonical graph matches a preset; other pathways are unchanged.
                custom[reviewed_id] = {**REACTANTS[reviewed_id], "hydrationStereoIssue": hydration_stereo_issue}
            if complete_alkyne_stereo_issue:
                custom[reviewed_id] = {**custom.get(reviewed_id, REACTANTS[reviewed_id]), "alkyneCompleteStereoIssue": complete_alkyne_stereo_issue}
            if halogen_alkyne_stereo_issue:
                custom[reviewed_id] = {**custom.get(reviewed_id, REACTANTS[reviewed_id]), "alkyneHalogenStereoIssue": halogen_alkyne_stereo_issue}
            if hx_alkyne_stereo_issue:
                custom[reviewed_id] = {**custom.get(reviewed_id, REACTANTS[reviewed_id]), "alkyneHxStereoIssue": hx_alkyne_stereo_issue}
            ids.append(reviewed_id)
            continue
        if reagent_role(molecule) != "hypochlorite" and any(atom.GetSymbol() not in ALLOWED_ELEMENTS or atom.GetFormalCharge() or atom.HasQuery()
               or atom.GetNumRadicalElectrons() or atom.GetIsotope() for atom in molecule.GetAtoms()):
            raise ChemistryError("This structure is outside the supported neutral, non-radical molecule scope.")
        identifier = f"drawn-{slot + 1}"
        supplied_name = reference.get("name")
        custom[identifier] = {"name": supplied_name[:200] if isinstance(supplied_name, str) and supplied_name.strip() else "Drawn molecule", "smiles": canonical}
        if hydration_stereo_issue:
            custom[identifier]["hydrationStereoIssue"] = hydration_stereo_issue
        if partial_alkyne_stereo_issue:
            custom[identifier]["alkynePartialStereoIssue"] = partial_alkyne_stereo_issue
        if complete_alkyne_stereo_issue:
            custom[identifier]["alkyneCompleteStereoIssue"] = complete_alkyne_stereo_issue
        if halogen_alkyne_stereo_issue:
            custom[identifier]["alkyneHalogenStereoIssue"] = halogen_alkyne_stereo_issue
        if hx_alkyne_stereo_issue:
            custom[identifier]["alkyneHxStereoIssue"] = hx_alkyne_stereo_issue
        ids.append(identifier)
    return (ids[0], ids[1]), custom, interpretation_notes


class ConditionInputs(dict):
    """Retain unsupported field names for pathway-specific confidence checks.

    Values are deliberately not echoed or interpreted as new chemistry. The
    existing normalized string dictionary remains the serialization contract.
    """
    unsupported_fields = ()


def _conditions(raw: dict[str, str] | None) -> dict[str, str]:
    if raw is None:
        return {key: "" for key in CONDITION_VALUES}
    if not isinstance(raw, dict):
        raise ChemistryError("Choose the reaction conditions from the available options.")
    result = ConditionInputs()
    # Namespaced declaration is consumed ONLY by secondary oxidation. Keep it
    # unknown to other pathways, preserving their existing input assessment.
    result.secondary_oxidation_profile = getattr(raw,'secondary_oxidation_profile',raw.get(secondary_alcohol_oxidation_rule.PROFILE_KEY,''))
    result.unsupported_fields = tuple(sorted(str(k)[:120] for k in raw if k not in CONDITION_VALUES))
    for key, allowed in CONDITION_VALUES.items():
        value = raw.get(key, "")
        if not isinstance(value, str) or value not in allowed:
            raise ChemistryError(f"Unsupported condition value for '{key}'; choose from the available options. No new condition model is inferred.")
        result[key] = value
    return result


def _profile(reaction: dict[str, object]) -> dict[str, str]:
    return reaction["profile"]


def _assessment(reaction: dict[str, object], conditions: dict[str, str]) -> dict[str, object]:
    if reaction.get("secondaryOxidationModel"):
        assessment=secondary_alcohol_oxidation_rule.assess_conditions(reaction,conditions)
        assessment["evidence"]=addition_contract.evidence(reaction,assessment,conditions)
        return assessment
    if reaction.get("primaryOxidationModel"):
        assessment = primary_alcohol_oxidation_rule.assess_conditions(reaction, conditions)
        assessment["evidence"] = addition_contract.evidence(reaction, assessment, conditions)
        return assessment
    if reaction["mechanism"] in REVIEWED:
        assessment = assess_conditions(reaction, conditions)
        if reaction["mechanism"] in addition_contract.NET_PATHWAYS:
            assessment["evidence"] = addition_contract.evidence(reaction, assessment, conditions)
        return assessment
    profile = _profile(reaction)
    missing = [key for key, value in profile.items() if not conditions[key]]
    different = [key for key, value in profile.items() if conditions[key] and conditions[key] != value]
    if different:
        return {"state": "alternative", "note": "Selected conditions differ from this pathway's teaching example; it may still compete."}
    if missing:
        return {"state": "incomplete", "note": "Set the remaining conditions to compare this pathway."}
    if "catalyst" not in profile and conditions["catalyst"] in {"acid", "metal"}:
        return {"state": "incomplete", "note": "The required conditions align, but this additional catalyst is not evaluated for this pathway."}
    return {"state": "aligned", "note": "Selected conditions align with this reviewed pathway; this does not predict yield or certainty."}


def _reaction_is_balanced(reaction: dict[str, object], reactants: dict[str, dict[str, object]]) -> bool:
    """Check atom/charge balance; repeated IDs encode verified coefficients."""
    inputs = Counter()
    input_charge = 0
    for reactant_id in reaction.get("equationReactants", reaction["reactants"]):
        reactant = reactants.get(reactant_id)
        if reactant is None:
            return False
        inputs.update(_element_counts(reactant["smiles"]))
        input_charge += _formal_charge(reactant["smiles"])
    outputs = _element_counts(reaction["productSmiles"])
    output_charge = _formal_charge(reaction["productSmiles"])
    for byproduct in reaction["byproducts"]:
        outputs.update(_element_counts(byproduct["smiles"]))
        output_charge += _formal_charge(byproduct["smiles"])
    return bool(inputs) and inputs == outputs and input_charge == output_charge


def _calculator_input(reference: str | dict[str, str], resolved_id: str,
                      reactants: dict[str, dict[str, object]]) -> tuple[dict[str, object], str | None]:
    """Keep the selected reagent's identity when its spectator ion is omitted."""
    resolved = reactants[resolved_id]
    source = REACTANTS[reference] if isinstance(reference, str) and reference in REACTANTS else resolved
    smiles = reference["smiles"] if isinstance(reference, dict) else source["smiles"]
    molecule = _molecule(smiles)
    name = source["name"]
    formula = source.get("formula", _formula(smiles))
    if isinstance(reference, dict):
        formula = _formula(smiles)
        supplied_name = reference.get("name")
        if isinstance(supplied_name, str) and supplied_name.strip() and len(supplied_name) <= 200:
            name = supplied_name.strip()
    counterion = _hydroxide_from_salt(molecule) if resolved_id == "hydroxide" else None
    note = None
    if counterion:
        names = {"Li": "Lithium", "Na": "Sodium", "K": "Potassium", "Rb": "Rubidium", "Cs": "Caesium"}
        name = f"{names[counterion]} hydroxide"
        formula = f"{counterion}OH"
        note = f"{name}: 1 mol supplies 1 mol OH⁻. Its full salt molar mass is used; the spectator {counterion}⁺ is omitted from the net equation."
    return {"name": name, "formula": formula, "molarMass": round(Descriptors.MolWt(molecule), 6)}, note


def _reaction_stoichiometry(reaction: dict[str, object], reactants: dict[str, dict[str, object]],
                            pair_ids: tuple[str, str] | None = None,
                            originals: tuple[str | dict[str, str], str | dict[str, str]] | None = None) -> dict[str, object]:
    """Serialize the selected pathway's trusted calculation basis and roles."""
    pair_ids = pair_ids or tuple(reaction["reactants"])
    originals = originals or pair_ids
    consumed = Counter(reaction.get("equationReactants", reaction["reactants"]))
    included = []
    excluded = []
    notes = ["Theoretical maximum for this pathway at complete conversion; not a predicted or actual yield."]
    for slot, (resolved_id, original) in enumerate(zip(pair_ids, originals)):
        item, salt_note = _calculator_input(original, resolved_id, reactants)
        if resolved_id in consumed:
            coefficient = consumed.pop(resolved_id)
            included.append({"inputSlot": slot, **item, "coefficient": coefficient})
            if salt_note:
                notes.append(salt_note)
        else:
            excluded.append({"inputSlot": slot, "name": item["name"],
                             "reason": "Acid catalyst; regenerated, not consumed in this net equation." if reaction["mechanism"] == "Alcohol dehydration" else "Solvent / medium; not consumed in this net equation."})
    balanced = not consumed and _reaction_is_balanced(reaction, reactants)
    if reaction.get("profile", {}).get("catalyst") in {"acid", "metal"}:
        notes.append("Catalyst amounts are excluded: the catalyst is not consumed in the net equation.")
    if reaction["mechanism"] in {"Esterification", "Ester hydrolysis"}:
        notes.append("This reversible reaction may not reach complete conversion.")
    if reaction["mechanism"] == "Alcohol dehydration":
        notes.append("One alcohol gives one alkene plus one water. Acid is catalytic and excluded from amounts. Reversibility, ether formation, isomerization and selective mono-dehydration are not predicted; alternative products must not be summed as yields.")
    if reaction["mechanism"] == "Polymerization model":
        notes.append("Calculation describes only the selected finite, phenyl-ended oligomer model, not bulk-polymer yield or molecular weight. Benzoyl peroxide is consumed as initiator.")
    if reaction["mechanism"] == "SN1":
        notes.append("One water equivalent in the simplified alcohol + HX net reporting equation. Additional water is solvent/proton-transfer medium; the mechanism shows hydronium + halide. This is not a prescription for solvent quantity, isolated conversion or racemization ratio.")
    if reaction["mechanism"] == "E1":
        notes.append("Water is solvent/base and excluded from the simplified alkene + HX net calculation. The explicit aqueous mechanism shows hydronium + halide. This describes one selected elimination site, not solvent quantity, selective mono-conversion, major-product or E/Z ratios.")
    if reaction["mechanism"] == "Hydration":
        notes.append("One water equivalent is consumed at the selected C=C. Acid is regenerated and excluded. Amounts are conditional on supported acid activation and describe theoretical net conversion, not equilibrium yield, regioisomer ratios or selective one-site conversion.")
    if reaction["mechanism"] == "Hydrohalogenation":
        notes.append("One actual HX equivalent supplies both H and halogen and is consumed; HX is not a regenerated acid catalyst. Amounts describe a selected conditional ionic net option, not selective mono-addition, regio/stereoisomer ratios or an actual experimental yield.")
    if reaction["mechanism"] == "Bromination":
        notes.append("One actual Br2 equivalent is consumed per selected C=C, with no net byproduct. Each stereochemical alternative is a separate complete-conversion upper bound, not an amount to add across alternatives or a stereoisomer ratio. Non-nucleophilic model conditions are required; actual yield and selective mono-bromination are not predicted.")
    if reaction["mechanism"] == "Epoxidation":
        notes.append("One actual peroxyacid equivalent transfers one O to one selected C=C and gives one equivalent of its actual carboxylic acid coproduct. Each face/site alternative is a separate theoretical bound, not an amount to sum or a stereoisomer ratio. Peroxyacid is consumed, not a catalyst; subsequent epoxide opening and isolated yields are not predicted.")
    if reaction["mechanism"] == "Alkene dihydroxylation":
        notes.append("One H2O2 equivalent per selected C=C balances the explicit net diol graph. Os catalyst and aqueous release species are omitted, not consumed calculated reagents. Formal O/H maps are not catalyst oxygen/proton-exchange provenance. Amounts are conditional theoretical net upper bounds, not actual yield, stereo ratios or selective mono-oxidation.")
    if reaction["mechanism"] == "Chlorination":
        notes.append("One actual Cl2 equivalent is consumed per selected C=C, with no net byproduct. Each stereochemical alternative is a separate complete-conversion upper bound, not an amount to add across alternatives or a stereoisomer ratio. Non-nucleophilic model conditions are required; actual yield and selective mono-chlorination are not predicted.")
    if not balanced:
        notes.append("Calculation unavailable: the net equation has not passed atom and charge balance checks.")
    return {
        "balanced": balanced,
        "reactants": included,
        "product": {"name": reaction["productName"], "formula": _formula(reaction["productSmiles"]),
                    "molarMass": round(Descriptors.MolWt(_molecule(reaction["productSmiles"])), 6), "coefficient": 1},
        "excludedInputs": excluded,
        "notes": notes,
    }


def _serialize_reaction(reaction_id: str, reaction: dict[str, object], conditions: dict[str, str] | None = None,
                        *, custom_reactants: dict[str, dict[str, object]] | None = None,
                        pair_ids: tuple[str, str] | None = None,
                        originals: tuple[str | dict[str, str], str | dict[str, str]] | None = None) -> dict[str, object]:
    information = reaction_information(reaction)
    payload = {
        "id": reaction_id, "name": reaction["name"], "family": reaction["family"], "mechanism": reaction["mechanism"],
        "productSmiles": reaction["productSmiles"], "site": reaction.get("site"),
        "reactants": reaction["reactants"],
        "equationReactants": reaction.get("equationReactants", reaction["reactants"]),
        "productName": reaction["productName"], "productFormula": _formula(reaction["productSmiles"]),
        "productEquationFormula": reaction.get("productEquationFormula", _formula(reaction["productSmiles"])),
        "byproducts": [{"name": item["name"], "formula": item.get("formula", _formula(item["smiles"]))} for item in reaction["byproducts"]],
        "conditions": reaction["conditions"], "explanation": reaction["explanation"], "sourceUrl": reaction["sourceUrl"],
        "stoichiometry": _reaction_stoichiometry(reaction, {**REACTANTS, **(custom_reactants or {})}, pair_ids, originals),
        **({"aldehydeOxidationModel": reaction["aldehydeOxidationModel"]} if reaction.get("aldehydeOxidationModel") else {}),
        "reasoning": explain_pathway(reaction, {**REACTANTS, **(custom_reactants or {})}, conditions),
        "information": information,
        "classifications": information["classifications"],
        **({"dehydrationModel": reaction["dehydrationModel"], "stereochemistry": reaction["stereochemistry"]} if reaction["mechanism"] == "Alcohol dehydration" else {}),
        **({"alcoholSubstitutionModel": reaction["alcoholSubstitutionModel"], "stereochemistry": reaction["stereochemistry"]} if reaction["mechanism"] == "Alcohol substitution" else {}),
        **({"primaryOxidationModel": reaction["primaryOxidationModel"], "stereochemistry": reaction["stereochemistry"]} if reaction.get("primaryOxidationModel") else {}),
        **({"secondaryOxidationModel": reaction["secondaryOxidationModel"], "stereochemistry": reaction["stereochemistry"]} if reaction.get("secondaryOxidationModel") else {}),
        **({"compatibility": reaction["compatibility"]} if reaction.get("compatibility") else {}),
        **({"regioselectivity": reaction["regioselectivity"], "stereochemistry": reaction["stereochemistry"]} if reaction["mechanism"] == "Hydration" else {}),
        **({"regioselectivity": reaction["regioselectivity"], "stereochemistry": reaction["stereochemistry"], "hxModel": reaction["hxModel"]} if reaction["mechanism"] == "Hydrohalogenation" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "epoxidationStereo": reaction["epoxidationStereo"]} if reaction["mechanism"] == "Epoxidation" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "dihydroxylationStereo": reaction["dihydroxylationStereo"]} if reaction["mechanism"] == "Alkene dihydroxylation" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "chlorinationStereo": reaction["chlorinationStereo"]} if reaction["mechanism"] == "Chlorination" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "brominationStereo": reaction["brominationStereo"]} if reaction["mechanism"] == "Bromination" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "alkynePartialStereo": reaction["alkynePartialStereo"]} if reaction["mechanism"] == "Alkyne partial hydrogenation" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "alkyneCompleteModel": reaction["alkyneCompleteModel"]} if reaction["mechanism"] == "Alkyne hydrogenation" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "alkyneHalogenModel": reaction["alkyneHalogenModel"]} if reaction["mechanism"] == "Alkyne halogenation" else {}),
        **({"stereochemistry": reaction["stereochemistry"], "alkyneHxModel": reaction["alkyneHxModel"], "regioselectivity": reaction["regioselectivity"]} if reaction["mechanism"] == "Alkyne hydrohalogenation" else {}),
    }
    if conditions is not None:
        payload["assessment"] = _assessment(reaction, conditions)
        guidance = guided_condition_metadata(reaction_id, reaction, payload["assessment"], conditions)
        if guidance is not None:
            payload["guidedConditions"] = guidance
    if reaction["mechanism"] in addition_contract.NET_PATHWAYS or reaction.get("primaryOxidationModel") or reaction.get("secondaryOxidationModel"):
        context = _conditions(conditions)
        assessment = payload.get("assessment") or _assessment(reaction, context)
        payload["stoichiometry"]["context"] = addition_contract.calculation_context(
            reaction, assessment, context, payload["stoichiometry"]["notes"])
    return payload


def reaction_catalog() -> dict[str, object]:
    return {
        "reactants": [
            {
                "id": key, "name": value["name"],
                "formula": value.get("formula", _formula(value["smiles"])),
                "smiles": Chem.MolToSmiles(_molecule(value["smiles"]), canonical=True),
                "aliases": value["aliases"],
            }
            for key, value in REACTANTS.items()
        ],
        "reactions": [_serialize_reaction(key, value) for key, value in _all_reactions().items()],
    }


def inspect_reactant(reactant, include_3d=False):
    return inspect_structure(reactant, REACTANTS, include_3d, analyze_molfile)


def match_reactions(reactant_a: str | dict[str, str], reactant_b: str | dict[str, str], conditions: dict[str, str] | None = None) -> dict[str, object]:
    pair_ids, custom, interpretation_notes = _resolve_reactants(reactant_a, reactant_b)
    context = _conditions(conditions)
    pair = sorted(pair_ids)
    generated, unsupported = _reactions_for_pair(*pair_ids, {**REACTANTS, **custom}, context)
    matches = [
        _serialize_reaction(key, value, context, custom_reactants=custom, pair_ids=pair_ids,
                            originals=(reactant_a, reactant_b))
        for key, value in generated.items()
        if sorted(value["reactants"]) == pair
    ]
    options = addition_contract.grouped_options(matches, {**REACTANTS, **custom})
    conditional = bool(matches) and all(r["mechanism"] in addition_contract.NET_PATHWAYS or r.get("primaryOxidationModel") or r.get("secondaryOxidationModel") for r in matches)
    comparison = compare_pathways(options)
    if comparison:
        for column, option in zip(comparison["columns"], options):
            column["label"] = option.get("assessment", {}).get("evidence", {}).get("label", column["label"])
    return {"contractVersion": 2, "reactions": matches, "reactionOptions": options,
            "reactionsContract": "Legacy independently addressable sites; use reactionOptions for grouped product choices.",
            "optionCounts": addition_contract.option_counts(options),
            "interpretationNotes": interpretation_notes, "unsupportedReasons": unsupported,
            "structuralEligibility": "eligible" if matches else "unsupported",
            "supportState": "Conditional" if conditional else "Supported" if matches else "Unsupported",
            "comparison": comparison}


def reaction_diagram(reaction_id: str, reactant_a: str | dict[str, str], reactant_b: str | dict[str, str], conditions: dict[str, str] | None = None) -> dict[str, object]:
    """Preview verified net structures without running the 3D calculation."""
    pair_ids, custom, interpretation_notes = _resolve_reactants(reactant_a, reactant_b)
    context = _conditions(conditions)
    reaction = _reactions_for_pair(*pair_ids, {**REACTANTS, **custom}, context)[0].get(reaction_id)
    if not reaction or sorted(reaction["reactants"]) != sorted(pair_ids):
        raise ChemistryError("Choose a reaction that matches both selected molecules.")
    diagram = build_reaction_diagram(reaction, {**REACTANTS, **custom})
    if reaction["mechanism"] == "Aldehyde oxidation":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["aldehydeOxidationModel"] = reaction["aldehydeOxidationModel"]
        diagram["note"] = diagram["assessment"]["note"] + " Formal net mapping only; no full oxidation mechanism or acidification step is depicted."
    if reaction["mechanism"] == "Alkyne hydrohalogenation":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["alkyneHxModel"] = reaction["alkyneHxModel"]
        diagram["note"] = "Conditional ionic alkyne HX net equation. " + diagram["assessment"]["note"] + " " + reaction["alkyneHxModel"]["note"] + " No complete vinyl-cation/radical mechanism or experimental stopping/selectivity is asserted."
    if reaction["mechanism"] == "Alkyne halogenation":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["alkyneHalogenModel"] = reaction["alkyneHalogenModel"]
        diagram["note"] = "Conditional alkyne X2 net equation. " + diagram["assessment"]["note"] + " " + reaction["alkyneHalogenModel"]["note"] + " No complete mapped halonium mechanism or stable vinyl carbocation is asserted."
    if reaction["mechanism"] == "Alkyne hydrogenation":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["alkyneCompleteModel"] = reaction["alkyneCompleteModel"]
        diagram["note"] = "Conditional complete alkyne hydrogenation net model. " + diagram["assessment"]["note"] + " " + reaction["alkyneCompleteModel"]["note"] + " No catalytic surface mechanism or discrete ionic/radical intermediates are implemented."
    if reaction["mechanism"] == "Alkyne partial hydrogenation":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["alkynePartialStereo"] = reaction["alkynePartialStereo"]
        diagram["note"] = "Conditional Lindlar net option. " + diagram["assessment"]["note"] + " " + reaction["alkynePartialStereo"]["note"] + " No catalytic surface mechanism or discrete ionic/radical intermediates are implemented."
    if reaction["mechanism"] == "Alkene dihydroxylation":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["dihydroxylationStereo"] = reaction["dihydroxylationStereo"]
        diagram["note"] = "Conditional syn dihydroxylation net option. " + diagram["assessment"]["note"] + " " + reaction["dihydroxylationStereo"]["note"]
    if reaction["mechanism"] == "Epoxidation":
        assessment = _assessment(reaction, context)
        diagram["assessment"] = assessment
        diagram["epoxidationStereo"] = reaction["epoxidationStereo"]
        diagram["note"] = "Conditional peroxyacid epoxidation. " + assessment["note"] + " " + reaction["epoxidationStereo"]["note"] + " The mapped mechanism is one formal concerted oxygen transfer; no stable intermediate or secondary ring opening is inferred."
    if reaction["mechanism"] == "Bromination":
        assessment = _assessment(reaction, context)
        diagram["assessment"] = assessment
        diagram["brominationStereo"] = reaction["brominationStereo"]
        diagram["note"] = ("Conditional Br2 net option. " + assessment["note"] + " " +
                           "Wedges/dashes show assigned local configurations where validated; " + reaction["brominationStereo"]["outcome"] +
                           ". Dots show supported lone pairs, not spatial orientation. Anti describes addition geometry, not a universal trans label. A complete bromonium mechanism and product ratios are not modeled.")
    if reaction["mechanism"] == "Chlorination":
        assessment = _assessment(reaction, context)
        diagram["assessment"] = assessment
        diagram["chlorinationStereo"] = reaction["chlorinationStereo"]
        diagram["note"] = ("Conditional Cl2 net option. " + assessment["note"] + " " +
                           "Wedges/dashes show assigned local configurations where validated; " + reaction["chlorinationStereo"]["outcome"] +
                           ". Dots show supported lone pairs, not spatial orientation. Anti describes addition geometry, not a universal trans label. A complete chloronium mechanism and product ratios are not modeled.")
    if reaction["mechanism"] == "Alcohol dehydration":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["dehydrationModel"] = reaction["dehydrationModel"]
        diagram["note"] = "Conditional dehydration net option. " + diagram["assessment"]["note"] + " " + reaction["dehydrationModel"]["provenance"] + " No complete mapped acid cycle/proton-transfer mechanism is implemented; bare OH departure is not an elementary step."
    if reaction["mechanism"] == "Alcohol substitution":
        diagram["assessment"] = _assessment(reaction, context)
        diagram["alcoholSubstitutionModel"] = reaction["alcoholSubstitutionModel"]
        diagram["note"] = "Conditional activated-HX net substitution. " + diagram["assessment"]["note"] + " " + reaction["alcoholSubstitutionModel"]["provenance"] + " No complete mapped protonation/water-departure/capture mechanism is implemented; net C–O cleavage is not bare OH departure."
    if reaction.get("primaryOxidationModel"):
        diagram["assessment"] = _assessment(reaction, context)
        diagram["primaryOxidationModel"] = reaction["primaryOxidationModel"]
        diagram["note"] = "Hypothetical primary-alcohol first-stage net equation, not an asserted aldehyde endpoint. " + diagram["assessment"]["note"] + " " + reaction["primaryOxidationModel"]["provenance"] + " No complete hypochlorite/catalyst mechanism is implemented; no H2 gas is generated."
    if reaction.get("secondaryOxidationModel"):
        diagram["assessment"]=_assessment(reaction,context)
        diagram["secondaryOxidationModel"]=reaction["secondaryOxidationModel"]
        diagram["note"]="Secondary ketone net equation, not isolated product certainty. "+diagram["assessment"]["note"]+" "+reaction["secondaryOxidationModel"]["provenance"]+" No complete mapped oxidation mechanism is implemented."
    if reaction["mechanism"] == "Hydration":
        assessment = _assessment(reaction, context)
        diagram["assessment"] = assessment
        diagram["note"] = ("Conditional net hydration option. " + assessment["note"] + " " if not assessment["canRun"] else "") + diagram["note"]
    if reaction["mechanism"] == "Hydrohalogenation":
        assessment = _assessment(reaction, context)
        diagram["assessment"] = assessment
        diagram["note"] = "Conditional ionic HX net option. " + assessment["note"] + " " + diagram["note"]
    return {**diagram,
            "mechanism": build_mechanism(reaction, {**REACTANTS, **custom}),
            "interpretationNotes": interpretation_notes}


def run_curated_reaction(reaction_id: str, reactant_a: str | dict[str, str], reactant_b: str | dict[str, str], conditions: dict[str, str] | None = None) -> dict[str, object]:
    pair_ids, custom, interpretation_notes = _resolve_reactants(reactant_a, reactant_b)
    context = _conditions(conditions)
    reaction = _reactions_for_pair(*pair_ids, {**REACTANTS, **custom}, context)[0].get(reaction_id)
    if not reaction or sorted(reaction["reactants"]) != sorted(pair_ids):
        raise ChemistryError("Choose a reaction that matches both selected molecules.")

    if reaction["mechanism"] == "Aldehyde oxidation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect conditional 2D; no qualified 3D reporting product is available for these inputs.")

    if reaction.get("primaryOxidationModel"):
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Primary oxidation remains conditional 2D only; no final aldehyde 3D product is asserted.")
    if reaction.get("secondaryOxidationModel"):
        assessment=_assessment(reaction,context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"]+" Secondary oxidation remains conditional 2D for this context; no qualified ketone 3D is asserted.")

    if reaction["mechanism"] == "Alcohol dehydration":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect conditional 2D; no 3D dehydration outcome is asserted for this context.")
    if reaction["mechanism"] == "Alcohol substitution":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect conditional 2D; no 3D HX substitution outcome is asserted for this context.")
    if reaction["mechanism"] == "Hydration":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D net option or select supported acid/water conditions before generating its 3D product.")
    if reaction["mechanism"] == "Hydrohalogenation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Only the conditional 2D ionic HX net option is available for these settings; no 3D product is inferred.")

    if reaction["mechanism"] == "Bromination":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D net option; no 3D dibromide is inferred for these conditions.")
    if reaction["mechanism"] == "Epoxidation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D mechanism; no isolated 3D epoxide is inferred for these settings.")
    if reaction["mechanism"] == "Chlorination":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D net option; no 3D dichloride is inferred for these conditions.")

    if reaction["mechanism"] == "Alkene dihydroxylation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Only the conditional 2D net diol option is available.")
    if reaction["mechanism"] == "Alkyne partial hydrogenation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D net option; no 3D Lindlar alkene is inferred for these settings.")
    if reaction["mechanism"] == "Alkyne hydrogenation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D net equation; no 3D complete-reduction outcome is asserted for these settings.")
    if reaction["mechanism"] == "Alkyne halogenation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D net equation; no selected 3D halogenation outcome is asserted for these settings.")
    if reaction["mechanism"] == "Alkyne hydrohalogenation":
        assessment = _assessment(reaction, context)
        if not assessment["canRun"]:
            raise ChemistryError(assessment["note"] + " Inspect the conditional 2D HX net equation; no selected 3D hydrohalogenation outcome is asserted for these settings.")
    if not _reaction_is_balanced(reaction, {**REACTANTS, **custom}):
        raise RuntimeError(f"Curated reaction {reaction_id} is not atom- and charge-balanced.")

    # Reuse the verified mapped graph used by the 2D diagram. Explicit-H atom
    # order survives Molfile loading, embedding, and geometry optimization.
    product = mapped_product_molecule(reaction, {**REACTANTS, **custom})
    return {
        "productName": reaction["productName"],
        "product": analyze_molfile(Chem.MolToMolBlock(product)),
        "balanced": True,
        "assessment": _assessment(reaction, context),
        "interpretationNotes": interpretation_notes,
    }


def _unmapped_smiles(molecule: Chem.Mol) -> str:
    """Keep atom identities in geometry, while showing ordinary chemistry text."""
    copy = Chem.Mol(molecule)
    for atom in copy.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(Chem.RemoveHs(copy), canonical=True, isomericSmiles=True)


def analyze_molfile(molfile: str) -> dict[str, object]:
    if not molfile.strip():
        raise ChemistryError("Draw a molecule before generating its 3D model.")
    if len(molfile) > MAX_BODY_BYTES:
        raise ChemistryError("That drawing is too large for the current Builder.")

    molecule = Chem.MolFromMolBlock(molfile, sanitize=False, removeHs=False)
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise ChemistryError("The drawing could not be read as a molecule.")
    if molecule.GetNumAtoms() > MAX_ATOMS:
        raise ChemistryError(f"The current Builder supports at most {MAX_ATOMS} drawn atoms.")
    for atom in molecule.GetAtoms():
        if atom.HasQuery():
            raise ChemistryError("Replace query atoms with specific elements before generating 3D.")
        if atom.GetSymbol() not in BUILDER_3D_ELEMENTS:
            # A periodic-table atom placed alone in Ketcher has no drawn H.
            # The Molfile can carry a computed H count even though no H was
            # drawn. RDKit otherwise reports e.g. NaH for a bare Na atom.
            atom.SetNumExplicitHs(0)
            atom.SetNoImplicit(True)

    try:
        Chem.SanitizeMol(molecule)
    except Exception as exc:
        overfilled = re.search(r"Explicit valence for atom # \d+ ([A-Za-z]+), \d+, is greater than permitted", str(exc))
        if overfilled:
            element = ELEMENT_NAMES.get(overfilled.group(1), overfilled.group(1))
            raise ChemistryError(f"{element} has too many bonds in this drawing. Remove or change a bond, then try again.") from exc
        raise ChemistryError("This drawing has an invalid bond or valence. Check the atoms and their bonds, then try again.") from exc

    smiles = _unmapped_smiles(molecule)
    base = {
        "formula": rdMolDescriptors.CalcMolFormula(molecule),
        "molarMass": round(Descriptors.MolWt(molecule), 3),
        "smiles": smiles,
        "atoms": molecule.GetNumAtoms(),
        "bonds": molecule.GetNumBonds(),
    }
    reason = None
    if len(Chem.GetMolFrags(molecule)) != 1:
        reason = "This drawing has separate components. The 2D editor can show them, but one molecular 3D conformer would be misleading."
    elif any(atom.GetFormalCharge() for atom in molecule.GetAtoms()):
        reason = "This drawing contains charged atoms. Ionic structures remain 2D-only in this Builder."
    elif any(atom.GetSymbol() not in BUILDER_3D_ELEMENTS for atom in molecule.GetAtoms()):
        reason = "This drawing contains an element outside the Builder's covalent 3D scope. Metal or coordination bonding needs a different geometry method."
    elif any(atom.GetNumRadicalElectrons() for atom in molecule.GetAtoms()):
        reason = "This drawing contains a radical. The current 3D method does not cover its electronic state."
    if reason:
        return {**base, "representation": "2d-only", "reason": reason}

    molecule = Chem.AddHs(molecule)
    settings = AllChem.ETKDGv3()
    settings.randomSeed = 42
    settings.maxIterations = 200
    try:
        embedded = AllChem.EmbedMolecule(molecule, settings) == 0
    except Exception:
        embedded = False
    if not embedded:
        return {**base, "representation": "2d-only", "reason": "A reliable 3D shape could not be generated for this drawing."}

    try:
        if AllChem.MMFFHasAllMoleculeParams(molecule):
            force_field = "MMFF94"
            optimization_status = AllChem.MMFFOptimizeMolecule(molecule, maxIters=300)
        elif AllChem.UFFHasAllMoleculeParams(molecule):
            force_field = "UFF"
            optimization_status = AllChem.UFFOptimizeMolecule(molecule, maxIters=300)
        else:
            return {**base, "representation": "2d-only", "reason": "No supported force field is available for this structure; the 2D drawing is retained."}
    except Exception:
        return {**base, "representation": "2d-only", "reason": "3D optimization failed for this structure; the 2D drawing is retained."}

    return {
        "representation": "3d",
        "molfile": Chem.MolToMolBlock(molecule),
        "formula": rdMolDescriptors.CalcMolFormula(molecule),
        "molarMass": round(Descriptors.MolWt(molecule), 3),
        "smiles": _unmapped_smiles(molecule),
        "atoms": molecule.GetNumAtoms(),
        "bonds": molecule.GetNumBonds(),
        "forceField": force_field,
        "converged": optimization_status == 0,
        "atomLinks": [{"index": atom.GetIdx(), "mapId": atom.GetAtomMapNum(), "element": atom.GetSymbol()}
                      for atom in molecule.GetAtoms() if atom.GetAtomMapNum() > 0],
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict[str, object], code: int) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_structure(self, structure: str) -> None:
        data = structure.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "chemical/x-mdl-sdfile; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_png(self, data: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/api/reactions/catalog":
            self._send_json(reaction_catalog(), 200)
            return
        if parsed.path == "/api/pubchem/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            try:
                self._send_json(search_pubchem(query), 200)
            except PubChemError as exc:
                self._send_json({"error": str(exc)}, 503)
            return
        if parsed.path in ("/api/pubchem/structure", "/api/pubchem/depiction"):
            raw_cid = parse_qs(parsed.query).get("cid", [""])[0]
            if not raw_cid.isdecimal() or len(raw_cid) > 10 or int(raw_cid) <= 0:
                self._send_json({"error": "Choose a valid PubChem compound."}, 422)
                return
            try:
                cid = int(raw_cid)
                if parsed.path == "/api/pubchem/depiction":
                    depiction = get_pubchem_depiction(cid)
                    if depiction:
                        self._send_png(depiction)
                    else:
                        self._send_json({"error": "A 2D depiction is not available for this PubChem compound."}, 404)
                    return
                structure = get_pubchem_structure(cid)
                if structure is None:
                    smiles = get_pubchem_smiles(cid)
                    molecule = Chem.MolFromSmiles(smiles) if smiles else None
                    if molecule is not None:
                        try:
                            generated = analyze_molfile(Chem.MolToMolBlock(molecule))
                            structure = generated.get("molfile") if generated["representation"] == "3d" else None
                        except ChemistryError:
                            pass
                if structure:
                    self._send_structure(structure)
                else:
                    self._send_json({"error": "A 3D structure is not available for this PubChem compound."}, 404)
            except PubChemError as exc:
                self._send_json({"error": str(exc)}, 503)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path not in ("/api/chemistry", "/api/reactions/match", "/api/reactions/run", "/api/reactions/diagram", "/api/reactions/inspect"):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ChemistryError("The drawing request is empty or too large.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ChemistryError("Expected a molecule request.")
            if self.path == "/api/chemistry":
                if not isinstance(body.get("molfile"), str):
                    raise ChemistryError("Expected a molecule drawing in Molfile format.")
                payload = analyze_molfile(body["molfile"])
            elif self.path == "/api/reactions/inspect":
                payload = inspect_reactant(body.get("reactant"), body.get("include3D", False))
            else:
                if self.path != "/api/reactions/match" and not isinstance(body.get("reactionId"), str):
                    raise ChemistryError("Choose two molecules and a matching reaction.")
                if not all(isinstance(body.get(key), (str, dict)) for key in ("reactantA", "reactantB")):
                    raise ChemistryError("Choose two molecules and a matching reaction.")
                if self.path == "/api/reactions/match":
                    payload = match_reactions(body["reactantA"], body["reactantB"], body.get("conditions"))
                elif self.path == "/api/reactions/diagram":
                    payload = reaction_diagram(body["reactionId"], body["reactantA"], body["reactantB"], body.get("conditions"))
                else:
                    payload = run_curated_reaction(body["reactionId"], body["reactantA"], body["reactantB"], body.get("conditions"))
            code = 200
        except (ChemistryError, ValueError, TypeError) as exc:
            payload = {"error": str(exc)}
            code = 422
        except Exception as exc:
            self.log_error("Unexpected chemistry failure: %s", exc)
            payload = {"error": "The chemistry service could not process this drawing."}
            code = 500

        self._send_json(payload, code)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("RDKit chemistry service ready at http://127.0.0.1:8000", flush=True)
    server.serve_forever()
