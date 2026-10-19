"""Active-metal, two-H2 selected-alkyne net reduction, not a surface model.

Other alkynes are inspectable bookkeeping alternatives, not inert spectators:
their simultaneous reduction is unresolved and blocks a single-site 3D claim.
No permissions or stereo rules from selective Lindlar reduction are inherited.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

PATHWAY = "Alkyne hydrogenation"
SOURCE = "https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes"
LIMITATION = ("Two actual H2 equivalents saturate this selected isolated acyclic C≡C in a bounded active-metal net model. "
              "Catalyst-specific hydrogenolysis, pressure, completion, rates, yields and surface exchange are not predicted. "
              "Other reducible sites are not assumed inert; multiple-alkyne single-site products are conditional 2D bookkeeping only, not selective 3D outcomes.")


def input_stereo_issue(smiles, normalized):
    issue = stereo.stereo_scope_issue(normalized, "complete alkyne hydrogenation")
    if issue:
        return issue
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None:
        return "Complete alkyne hydrogenation cannot validate the supplied stereochemical annotations."
    original = [a for a in raw.GetAtoms() if a.GetAtomicNum() != 1]
    cleaned = [a for a in normalized.GetAtoms() if a.GetAtomicNum() != 1]
    if len(original) != len(cleaned) or any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                                         and (a.GetChiralTag() not in stereo.TETRAHEDRAL or b.GetChiralTag() not in stereo.TETRAHEDRAL)
                                         for a, b in zip(original, cleaned)):
        return "Invalid or unsupported specified centers cannot be silently removed during complete alkyne hydrogenation input normalization."
    if any(b.GetBondDir() != Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return "Directional annotations on a substrate without C=C are unsupported; saturated-product geometry is not invented."
    return None


def site_issue(molecule, site):
    if tuple(site) not in graph.find_alkynes(molecule) and tuple(reversed(site)) not in graph.find_alkynes(molecule):
        return "Complete alkyne hydrogenation needs a selected actual carbon–carbon triple bond."
    if molecule.GetBondBetweenAtoms(*site).IsInRing():
        return "Cyclic alkyne strain, surface adsorption and ring-specific reduction are outside this validated acyclic complete-hydrogenation model."
    for i in site:
        for neighbor in molecule.GetAtomWithIdx(i).GetNeighbors():
            if neighbor.GetIdx() in site or neighbor.GetAtomicNum() == 1:
                continue
            if neighbor.GetAtomicNum() != 6 or neighbor.GetIsAromatic() or neighbor.GetHybridization() != Chem.HybridizationType.SP3:
                return "Conjugated/aromatic-adjacent or directly heteroatom-substituted alkyne reduction needs separate active-metal compatibility validation."
    return None


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkyne":
        if set(indices) == set(site):
            return "reactive", "validated", "Two actual H2 molecules add four H: two to each selected alkyne carbon, giving C–C."
        if site_issue(molecule, indices) or group["distance"] < 4:
            return "rejected", "competition", "A nearby, conjugated or ring-bound additional alkyne has unresolved competing reduction/cyclization; no selective full-reduction product is asserted."
        return "alternative-site", "competition", "Another isolated C≡C can also hydrogenate under active-metal conditions. This selectable one-site equation is 2D bookkeeping only; it does not establish selective retention or complete reduction of all sites."
    if kind in {"alcohol", "ether"}:
        oxygen = next(molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8)
        carbons = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6]
        remote = min(len(Chem.GetShortestPath(molecule, oxygen.GetIdx(), i)) - 1 for i in site) >= 4
        ordinary = (not oxygen.IsInRing() and len(carbons) == (1 if kind == "alcohol" else 2)
                    and all(c.GetHybridization() == Chem.HybridizationType.SP3 and not c.GetIsAromatic()
                            and not graph.is_allylic_or_benzylic(c)
                            and sum(n.GetAtomicNum() == 8 for n in c.GetNeighbors()) == 1 for c in carbons))
        if not ordinary or not remote:
            return "rejected", "competition", f"Nearby/propargylic/benzylic, cyclic or acetal-like {kind} environments require separate active-metal adsorption/hydrogenolysis validation; distance alone does not certify inertness."
        return "preserved", "bounded", f"Screened remote saturated aliphatic {kind} bonds and applicable configurations are retained in this two-H2 net model, not guaranteed unchanged for arbitrary catalysts or forcing conditions."
    return "rejected", "competition", f"Additional {kind} can introduce competing reduction, hydrogenolysis or catalyst effects; selective complete reduction of only the chosen alkyne is not validated."


def additional_check(molecule, site):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i)) - 1 if atom.GetIdx() != i else 0 for i in site)
            if distance < 2:
                yield "near-site-stereo", "unvalidated", "A specified propargylic/near-site center needs separate active-metal compatibility validation; no configuration is silently removed.", [atom.GetIdx()]


POLICY = compatibility.SitePolicy("isolated-alkyne complete active-metal hydrogenation", frozenset({"C", "H", "O"}),
                                  site_issue, group_check, additional_check, added_atoms=4)


def assess(molecule, site):
    report = compatibility.assess_site(molecule, site, POLICY)
    report["singleSiteBookkeepingOnly"] = any(g["type"] == "alkyne" and g["disposition"] == "alternative-site" for g in report["groups"])
    return report


def participants(substrate, reagents, site):
    if len(reagents) != 2:
        raise ValueError("Complete alkyne hydrogenation requires exactly two actual H2 molecules, not one or an arbitrary donor.")
    pairs = []
    for reagent in reagents:
        atoms = list(reagent.GetAtoms())
        if (len(atoms) != 2 or reagent.GetNumBonds() != 1 or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
                or any(a.GetAtomicNum() != 1 or a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() for a in atoms)):
            raise ValueError("Each full-reduction equivalent must be an actual neutral H–H molecule; other donors/isotopes are unsupported.")
        pairs.append([a.GetAtomMapNum() for a in atoms])
    if len({m for pair in pairs for m in pair}) != 4:
        raise ValueError("The four incoming hydrogens require distinct reaction atom identities.")
    return {"alkyne": [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site], "hydrogenPairs": pairs}


def edit_contract(substrate, reagents, site):
    p = participants(substrate, reagents, site)
    return [{"atomMaps": p["alkyne"], "before": 3.0, "after": 1.0},
            *[{"atomMaps": pair, "before": 1.0, "after": None} for pair in p["hydrogenPairs"]],
            *[{"atomMaps": [carbon, hydrogen], "before": None, "after": 1.0} for pair in p["hydrogenPairs"] for carbon, hydrogen in zip(p["alkyne"], pair)]]


def validate(before, after, substrate, reagents, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    edits = edit_contract(substrate, reagents, site)
    compatibility.validate_edit_contract(before, after, edits, expected_fragments=1)
    indexed = {a.GetAtomMapNum(): a for a in after.GetAtoms()}
    ends = [indexed[m] for m in edits[0]["atomMaps"]]
    bond = after.GetBondBetweenAtoms(*(a.GetIdx() for a in ends))
    if bond.GetBondType() != Chem.BondType.SINGLE or bond.GetStereo() != Chem.BondStereo.STEREONONE:
        raise ValueError("The selected full-reduction site must be saturated C–C without residual pi bonding or E/Z.")
    if any(a.GetHybridization() != Chem.HybridizationType.SP3 or a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
           or sum(n.GetAtomicNum() == 1 for n in a.GetNeighbors()) < 2 for a in ends):
        raise ValueError("Former alkyne carbons must be saturated CH2/CH3, not newly invented stereocenters.")


def equivalent_sites(molecule, first, second):
    heavy = [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    work = Chem.RemoveHs(Chem.Mol(molecule))
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    a, b = [tuple(heavy.index(i) for i in site[:2]) for site in (first, second)]
    return any({match[a[0]], match[a[1]]} == set(b) for match in
               work.GetSubstructMatches(work, uniquify=False, useChirality=True, maxMatches=512))


def metadata(substrate, reagents, site, report):
    return {"version": 1, **participants(substrate, reagents, site), "hydrogenEquivalents": 2,
            "selectedBondProductOrder": 1, "newLocalStereochemistry": "not applicable: CH2/CH3",
            "singleSiteBookkeepingOnly": report["singleSiteBookkeepingOnly"], "surfaceMechanism": "not implemented",
            "note": "Two H2 equivalents fully saturate the selected site. Unaffected physical configurations and CIP are independently checked; coordinates do not assign experimental outcomes."}
