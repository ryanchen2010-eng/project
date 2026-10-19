"""Bounded Lindlar/H2 net syn reduction, not a catalytic surface mechanism.

New alkene geometry is constructed from the validated same-side H relationship,
never from an optimized conformer. Spectators use the shared exact edit/stereo
validator; only the newly formed C=C is separately authorized and checked here.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

PATHWAY = "Alkyne partial hydrogenation"
SOURCE = "https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes"
PRIMARY_SOURCE = "https://www.orgsyn.org/demo.aspx?prep=CV5P0880"
LIMITATION = ("One H2 per selected isolated acyclic C≡C is a conditional Lindlar net model, not experimental one-site selectivity or guaranteed stopping. "
              "Catalyst surface states, hydrogen exchange, pressure, conversion, isomerization and over-reduction are not modeled. "
              "No discrete ionic/radical intermediate, dissolving-metal reduction, facial ratio or experimental yield is predicted.")


def input_stereo_issue(smiles, normalized):
    """Retain a pathway-specific rejection before canonical SMILES drops CX.

    The unsanitized copy only checks annotation preservation, never chemistry.
    Other alkyne pathways do not inherit new permissions or input policy.
    """
    issue = stereo.stereo_scope_issue(normalized, "Lindlar partial hydrogenation")
    if issue:
        return issue
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None:
        return "Lindlar partial hydrogenation cannot validate the supplied stereochemical annotation."
    old = [a for a in raw.GetAtoms() if a.GetAtomicNum() != 1]
    new = [a for a in normalized.GetAtoms() if a.GetAtomicNum() != 1]
    if len(old) != len(new) or any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                                 and (a.GetChiralTag() not in stereo.TETRAHEDRAL or b.GetChiralTag() not in stereo.TETRAHEDRAL)
                                 for a, b in zip(old, new)):
        return "An invalid or unsupported specified center cannot be retained by Lindlar partial hydrogenation; no annotation is silently discarded."
    if any(b.GetBondDir() != Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return "Directional alkene annotations on a triple-bond/single-bond-only substrate are unsupported; no input geometry is silently assumed."
    return None


def site_issue(molecule, site):
    if tuple(site) not in graph.find_alkynes(molecule) and tuple(reversed(site)) not in graph.find_alkynes(molecule):
        return "The selected site must be an actual carbon–carbon triple bond."
    if molecule.GetBondBetweenAtoms(*site).IsInRing():
        return "Cyclic alkyne reduction needs ring-specific strain and alkene-geometry validation; it is outside this acyclic Lindlar model."
    for i in site:
        for neighbor in molecule.GetAtomWithIdx(i).GetNeighbors():
            if neighbor.GetIdx() in site or neighbor.GetAtomicNum() == 1:
                continue
            if (neighbor.GetAtomicNum() != 6 or neighbor.GetIsAromatic()
                    or neighbor.GetHybridization() != Chem.HybridizationType.SP3):
                return "Conjugated/aromatic-adjacent or directly heteroatom-substituted alkynes need a separate Lindlar compatibility assessment."
    return None


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkyne":
        if set(indices) == set(site):
            return "reactive", "validated", "One actual H2 adds syn at this selected C≡C, forming C=C."
        issue = site_issue(molecule, indices)
        if issue or group["distance"] < 4:
            return "rejected", "competition", "Another conjugated, ring-bound or nearby alkyne introduces unresolved multi-site reduction/cyclization; its compatibility is not established."
        return "alternative-site", "bounded", "Another well-separated isolated C≡C is retained in this theoretical single-site option; selective mono-reduction is not predicted."
    if kind in {"alcohol", "ether"}:
        oxygen = next(molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8)
        carbons = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6]
        ordinary = (not oxygen.IsInRing() and len(carbons) == (1 if kind == "alcohol" else 2)
                    and all(c.GetHybridization() == Chem.HybridizationType.SP3 and not c.GetIsAromatic()
                            and sum(n.GetAtomicNum() == 8 for n in c.GetNeighbors()) == 1
                            and not graph.is_allylic_or_benzylic(c) for c in carbons))
        distance = min(len(Chem.GetShortestPath(molecule, oxygen.GetIdx(), i)) - 1 for i in site)
        if not ordinary or distance < 4:
            return "rejected", "competition", f"Nearby, propargylic/benzylic, cyclic or multiple-oxygen {kind} environments need separate adsorption, hydrogenolysis and cyclization validation."
        return "preserved", "bounded", f"Screened remote saturated aliphatic {kind} bonds and specified configuration are retained in the net edit; this does not certify all catalyst/solvent combinations."
    return "rejected", "competition", f"Additional {kind} is outside the screened Lindlar spectator set; competing reduction, hydrogenolysis or catalyst effects are unresolved."


def additional_check(molecule, site):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i)) - 1 if atom.GetIdx() != i else 0 for i in site)
            if distance < 2:
                yield "near-site-stereo", "unvalidated", "A specified propargylic/near-site center needs separately validated directed/surface compatibility; no configuration is silently discarded.", [atom.GetIdx()]


POLICY = compatibility.SitePolicy("isolated-alkyne Lindlar partial hydrogenation", frozenset({"C", "H", "O"}),
                                  site_issue, group_check, additional_check, added_atoms=2)


def assess(molecule, site):
    report = compatibility.assess_site(molecule, site, POLICY)
    report["singleSiteBookkeepingOnly"] = any(g["type"] == "alkyne" and g["disposition"] == "alternative-site" for g in report["groups"])
    return report


def participants(substrate, reagent, site):
    hydrogens = list(reagent.GetAtoms())
    if (len(hydrogens) != 2 or reagent.GetNumBonds() != 1
            or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or any(a.GetAtomicNum() != 1 or a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() for a in hydrogens)):
        raise ValueError("Lindlar partial hydrogenation requires one actual neutral H–H molecule; other reducing reagents and isotopes are not enabled.")
    return {"alkyne": [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site],
            "hydrogens": [a.GetAtomMapNum() for a in hydrogens]}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, reagent, site)
    return [{"atomMaps": p["alkyne"], "before": 3.0, "after": 2.0},
            {"atomMaps": p["hydrogens"], "before": 1.0, "after": None},
            *[{"atomMaps": [c, h], "before": None, "after": 1.0} for c, h in zip(p["alkyne"], p["hydrogens"])]]


def assign_syn_geometry(editor, substrate, site):
    """Both non-H substituents are cis; in this C/H local scope that is Z."""
    numbers = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    atoms = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    bond = editor.GetBondBetweenAtoms(*(atoms[m].GetIdx() for m in numbers))
    endpoints = [bond.GetBeginAtom(), bond.GetEndAtom()]
    refs = [[n.GetIdx() for n in a.GetNeighbors() if n.GetAtomMapNum() not in numbers and n.GetAtomicNum() != 1] for a in endpoints]
    if all(len(r) == 1 for r in refs):
        bond.SetStereoAtoms(refs[0][0], refs[1][0])
        bond.SetStereo(Chem.BondStereo.STEREOZ)
        Chem.SetDoubleBondNeighborDirections(editor)
    elif any(len(r) > 1 for r in refs):
        raise ValueError("The new alkene has an unsupported local substitution pattern.")
    # A terminal CH2 end (including ethene) has no E/Z stereochemistry.


def _check_syn(after, substrate, reagent, site):
    p = participants(substrate, reagent, site)
    atoms = {a.GetAtomMapNum(): a for a in after.GetAtoms()}
    ends = [atoms[m] for m in p["alkyne"]]
    bond = after.GetBondBetweenAtoms(*(a.GetIdx() for a in ends))
    internal = all(graph.attached_hydrogens(substrate.GetAtomWithIdx(i)) == 0 for i in site)
    local = [x for x in stereo.inspect_stereochemistry(after)["alkenes"] if set(x["atomMaps"]) == set(p["alkyne"])]
    if internal:
        if len(local) != 1 or local[0]["assignment"] != "Z" or local[0]["cisTrans"] != "cis":
            raise ValueError("The independently reassigned internal Lindlar product must be cis/Z, not E or unsigned.")
    elif bond.GetStereo() != Chem.BondStereo.STEREONONE or local:
        raise ValueError("A terminal Lindlar alkene must not receive invented E/Z geometry.")
    for carbon, hydrogen in zip(p["alkyne"], p["hydrogens"]):
        if after.GetBondBetweenAtoms(atoms[carbon].GetIdx(), atoms[hydrogen].GetIdx()) is None:
            raise ValueError("Each incoming H must retain its actual H2 provenance at the selected carbon.")


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    edits = edit_contract(substrate, reagent, site)
    parser = Chem.SmilesParserParams(); parser.removeHs = False
    restored = Chem.MolFromSmiles(Chem.MolToSmiles(after), parser)
    if restored is None:
        raise ValueError("The mapped Lindlar product could not be restored.")
    for product in (after, restored):
        _check_syn(product, substrate, reagent, site)
        # The shared validator forbids arbitrary new stereo. Authorize only
        # this separately checked new double bond, leaving all other tags intact.
        unsigned = Chem.Mol(product)
        atoms = {a.GetAtomMapNum(): a for a in unsigned.GetAtoms()}
        bond = unsigned.GetBondBetweenAtoms(*(atoms[m].GetIdx() for m in edits[0]["atomMaps"]))
        bond.SetStereo(Chem.BondStereo.STEREONONE)
        for a in (bond.GetBeginAtom(), bond.GetEndAtom()):
            for adjacent in a.GetBonds():
                adjacent.SetBondDir(Chem.BondDir.NONE)
        compatibility.validate_edit_contract(before, unsigned, edits, expected_fragments=1)


def equivalent_sites(molecule, first, second):
    heavy = [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    work = Chem.RemoveHs(Chem.Mol(molecule))
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    a, b = [tuple(heavy.index(i) for i in site[:2]) for site in (first, second)]
    return any({match[a[0]], match[a[1]]} == set(b) for match in
               work.GetSubstructMatches(work, uniquify=False, useChirality=True, maxMatches=512))


def stereo_metadata(substrate, product, reagent, site):
    p = participants(substrate, reagent, site)
    internal = all(graph.attached_hydrogens(substrate.GetAtomWithIdx(i)) == 0 for i in site)
    return {"model": "Lindlar net syn addition", "alkyneAtomMaps": p["alkyne"], "hydrogenAtomMaps": p["hydrogens"],
            "singleSiteBookkeepingOnly": assess(substrate, site)["singleSiteBookkeepingOnly"],
            "outcome": "cis/Z alkene" if internal else "terminal alkene; E/Z not applicable",
            "assignment": "Z" if internal else None, "surfaceMechanism": "not implemented", "ratios": None,
            "note": "New C=C geometry follows net syn addition, independently CIP-checked; distant physical configurations are retained. Coordinates represent this assigned graph, not predicted catalyst selectivity."}
