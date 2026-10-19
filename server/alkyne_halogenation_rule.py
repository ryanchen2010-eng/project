"""Bounded X2/alkyne net additions; no fictitious vinyl-cation mechanism.

Br2 first-stage anti geometry is an explicitly qualified net relationship.
Cl2 stereospecificity is not borrowed from Br2: its first-stage geometry stays
unsigned, and no stereospecific 3D outcome is asserted by the generic selector.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

PATHWAY = "Alkyne halogenation"
SOURCE = "https://openstax.org/books/organic-chemistry/pages/9-3-reactions-of-alkynes-addition-of-hx-and-x2"
CHLORINE_SOURCE = "https://doi.org/10.1016/S0040-4020(01)82137-2"
LIMITATION = ("One or two actual Br2/Cl2 equivalents give distinct selected-site net equations, not measured conversion or a reagent-supply guarantee. "
              "Br2 first-stage anti geometry is a bounded relationship, not a universal stereoisomer ratio. Cl2 first-stage geometry is unassigned. "
              "Competing capture, radical chemistry and multi-site selectivity are not predicted. No complete halonium mechanism is implemented.")


def input_stereo_issue(smiles, normalized):
    issue = stereo.stereo_scope_issue(normalized, "alkyne halogenation")
    if issue:
        return issue
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None:
        return "Alkyne halogenation cannot validate the supplied stereochemical annotations."
    old = [a for a in raw.GetAtoms() if a.GetAtomicNum() != 1]
    new = [a for a in normalized.GetAtoms() if a.GetAtomicNum() != 1]
    if len(old) != len(new) or any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                                 and (a.GetChiralTag() not in stereo.TETRAHEDRAL or b.GetChiralTag() not in stereo.TETRAHEDRAL)
                                 for a, b in zip(old, new)):
        return "An invalid or unsupported specified center cannot be silently removed during alkyne halogenation normalization."
    if any(b.GetBondDir() != Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return "Directional annotations without a C=C are unsupported; no initial alkyne E/Z is assumed."
    return None


def site_issue(molecule, site):
    if tuple(site) not in graph.find_alkynes(molecule) and tuple(reversed(site)) not in graph.find_alkynes(molecule):
        return "Alkyne halogenation requires an actual selected C≡C, not C=C or HX addition."
    if molecule.GetBondBetweenAtoms(*site).IsInRing():
        return "Cyclic alkyne strain and ring-specific halogen capture/geometry need independent validation."
    for i in site:
        for n in molecule.GetAtomWithIdx(i).GetNeighbors():
            if n.GetIdx() in site or n.GetAtomicNum() == 1:
                continue
            if n.GetAtomicNum() != 6 or n.GetIsAromatic() or n.GetHybridization() != Chem.HybridizationType.SP3:
                return "Conjugated, aromatic-adjacent or directly heteroatom-substituted alkynes need separate electrophilic halogenation validation."
    return None


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkyne":
        if set(indices) == set(site):
            return "reactive", "validated", "The selected C≡C accepts the actual chosen X2 equivalents; no HX orientation rule is used."
        if site_issue(molecule, indices) or group["distance"] < 4:
            return "rejected", "competition", "A nearby, conjugated or ring-bound additional alkyne has unresolved competing halogenation/cyclization."
        return "alternative-site", "competition", "Another isolated C≡C can also consume halogen; this one-site equation is conditional 2D bookkeeping, not selective conversion or an all-sites product."
    if kind in {"alcohol", "ether"}:
        oxygen = next(molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8)
        distances = [len(Chem.GetShortestPath(molecule, oxygen.GetIdx(), i)) - 1 for i in site]
        size = min(distances) + 1
        if min(distances) <= 5:
            return "rejected", "competition", f"Nearby {kind} O atom {oxygen.GetIdx() + 1} can introduce intramolecular capture (shortest potential closure: {size} ring atoms); small-ring capture/activation and 5/6-membered halocyclization are not the selected dihalogenation model."
        carbons = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6]
        ordinary = (not oxygen.IsInRing() and len(carbons) == (1 if kind == "alcohol" else 2)
                    and all(c.GetHybridization() == Chem.HybridizationType.SP3 and not c.GetIsAromatic()
                            and not graph.is_allylic_or_benzylic(c)
                            and sum(n.GetAtomicNum() == 8 for n in c.GetNeighbors()) == 1 for c in carbons))
        if not ordinary:
            return "rejected", "competition", f"Cyclic, activated, benzylic/allylic or acetal-like {kind} capture/cleavage is unvalidated for this halogenation model."
        return "preserved", "bounded", f"Screened remote saturated {kind} is preserved in the conditional net graph; distance does not prove experimental inertness. Cl2/O compatibility has a separate output gate."
    return "rejected", "competition", f"Additional {kind} can compete in electrophilic halogenation/capture; retention is not validated by this selected-alkyne model."


def additional_check(molecule, site):
    rings = molecule.GetRingInfo().AtomRings()
    if len(rings) > 1 or any(len(r) > 8 or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6
                                            or molecule.GetAtomWithIdx(i).GetHybridization() != Chem.HybridizationType.SP3 for i in r) for r in rings):
        yield "complex-ring", "unvalidated", "Complex, heterocyclic or unsaturated ring environments need separate electrophilic halogenation/capture validation.", sorted({i for r in rings for i in r})
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i)) - 1 if atom.GetIdx() != i else 0 for i in site)
            if distance < 2:
                yield "near-site-stereo", "unvalidated", "A specified propargylic center needs independent directed/capture compatibility validation; its configuration is not silently discarded.", [atom.GetIdx()]


def assess(molecule, site):
    if len(site) != 3 or type(site[2]) is not int or site[2] not in {1, 2}:
        raise ValueError("Choose one or two X2 equivalents for this existing alkyne pathway.")
    policy = compatibility.SitePolicy("isolated-alkyne electrophilic halogenation", frozenset({"C", "H", "O"}),
                                      site_issue, group_check, additional_check, added_atoms=2 * site[2])
    result = compatibility.assess_site(molecule, site[:2], policy)
    for rejection in result["rejections"]:
        if rejection["code"] == "product-size":
            rejection["message"] = f"The halogenation product would exceed 80 explicit atoms including {2 * site[2]} incoming halogen atoms; no H is added."
    result["singleSiteBookkeepingOnly"] = any(g["type"] == "alkyne" and g["disposition"] == "alternative-site" for g in result["groups"])
    result["oxygenCompatibilityUnresolvedForCl2"] = any(g["type"] in {"alcohol", "ether"} and g["disposition"] == "preserved" for g in result["groups"])
    return result


def participants(substrate, reagents, site):
    if len(site) != 3 or type(site[2]) is not int or site[2] not in {1, 2} or len(reagents) != site[2]:
        raise ValueError("The selected one/two-equivalent stage requires exactly that many actual X2 molecules.")
    pairs, symbols = [], set()
    for reagent in reagents:
        atoms = list(reagent.GetAtoms())
        if (len(atoms) != 2 or reagent.GetNumBonds() != 1 or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
                or atoms[0].GetSymbol() not in {"Br", "Cl"} or atoms[0].GetSymbol() != atoms[1].GetSymbol()
                or any(a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() for a in atoms)):
            raise ValueError("Use actual neutral Br–Br or Cl–Cl, not HX, mixed halogens, donors or isotopes.")
        pairs.append([a.GetAtomMapNum() for a in atoms]); symbols.add(atoms[0].GetSymbol())
    flat = [m for pair in pairs for m in pair]
    if len(symbols) != 1 or len(set(flat)) != len(flat) or any(m <= 0 for m in flat):
        raise ValueError("Every actual halogen atom needs a unique positive map; mixed reagent equivalents are unsupported.")
    return {"alkyne": [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]],
            "halogenPairs": pairs, "halogen": next(iter(symbols)), "equivalents": site[2]}


def edit_contract(substrate, reagents, site):
    p = participants(substrate, reagents, site)
    return [{"atomMaps": p["alkyne"], "before": 3.0, "after": float(3 - site[2])},
            *[{"atomMaps": pair, "before": 1.0, "after": None} for pair in p["halogenPairs"]],
            *[{"atomMaps": [c, x], "before": None, "after": 1.0} for pair in p["halogenPairs"] for c, x in zip(p["alkyne"], pair)]]


def assign_geometry(editor, substrate, reagents, site, *, anti_model=False):
    p = participants(substrate, reagents, site)
    indexed = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    bond = editor.GetBondBetweenAtoms(*(indexed[m].GetIdx() for m in p["alkyne"]))
    bond.SetStereo(Chem.BondStereo.STEREONONE)
    if site[2] == 1 and p["halogen"] == "Br" and anti_model:
        refs = dict(zip(p["alkyne"], p["halogenPairs"][0]))
        bond.SetStereoAtoms(*(indexed[refs[a.GetAtomMapNum()]].GetIdx() for a in (bond.GetBeginAtom(), bond.GetEndAtom())))
        # TRANS is relative to the actual entering Br atoms, NOT a CIP label.
        bond.SetStereo(Chem.BondStereo.STEREOTRANS)
        Chem.SetDoubleBondNeighborDirections(editor)


def check_geometry(product, substrate, reagents, site, *, anti_model=False):
    p = participants(substrate, reagents, site)
    atoms = {a.GetAtomMapNum(): a for a in product.GetAtoms()}
    bond = product.GetBondBetweenAtoms(*(atoms[m].GetIdx() for m in p["alkyne"]))
    local = [s for s in stereo.inspect_stereochemistry(product)["alkenes"] if set(s["atomMaps"]) == set(p["alkyne"])]
    if site[2] == 1 and p["halogen"] == "Br" and anti_model:
        # Independently verify both first CIP priorities, then ask the full CIP
        # labeler to reassign the graph; map numbers cannot supply priorities.
        refs = dict(zip(p["alkyne"], p["halogenPairs"][0]))
        reference_atoms = list(bond.GetStereoAtoms())
        if bond.GetStereo() not in stereo.DOUBLE_STEREO or len(reference_atoms) != 2:
            raise ValueError("The qualified anti product is missing its explicit opposite-Br geometry.")
        opposite = bond.GetStereo() in {Chem.BondStereo.STEREOE, Chem.BondStereo.STEREOTRANS}
        for carbon, ref in zip((bond.GetBeginAtom(), bond.GetEndAtom()), reference_atoms):
            opposite ^= product.GetAtomWithIdx(ref).GetAtomMapNum() != refs[carbon.GetAtomMapNum()]
        if not opposite:
            raise ValueError("The incoming bromines do not have the declared anti relationship.")
        for c, x in refs.items():
            neighbors = [n for n in atoms[c].GetNeighbors() if n.GetAtomMapNum() not in p["alkyne"]]
            if len(neighbors) != 2 or max(neighbors, key=lambda a: a.GetAtomicNum()).GetAtomMapNum() != x:
                raise ValueError("The first-stage CIP-priority model cannot validate this local substitution environment.")
        if len(local) != 1 or local[0]["assignment"] != "E":
            raise ValueError("The qualified anti Br2 product must independently reassign E in this validated C/H local scope.")
    elif site[2] == 1:
        if bond.GetStereo() != Chem.BondStereo.STEREONONE or any(s["specified"] for s in local):
            raise ValueError("First-stage E/Z fidelity is unvalidated for this halogen/medium; leave it unassigned.")
    elif bond.GetStereo() != Chem.BondStereo.STEREONONE or local:
        raise ValueError("Two-equivalent saturation must not retain former alkene E/Z geometry.")
    if any(atoms[m].GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for m in p["alkyne"]):
        raise ValueError("No new local tetrahedral configurations may be invented.")


def validate(before, after, substrate, reagents, site, *, anti_model=False):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    edits = edit_contract(substrate, reagents, site)
    parser = Chem.SmilesParserParams(); parser.removeHs = False
    restored = Chem.MolFromSmiles(Chem.MolToSmiles(after), parser)
    if restored is None:
        raise ValueError("The mapped halogenation product could not be restored.")
    for product in (after, restored):
        check_geometry(product, substrate, reagents, site, anti_model=anti_model)
        # Authorize only the separately checked NEW alkene stereo, not any
        # distant stereo loss. All exact atom/bond/stereo validators stay strict.
        unsigned = Chem.Mol(product)
        ends = {a.GetAtomMapNum(): a for a in unsigned.GetAtoms()}
        bond = unsigned.GetBondBetweenAtoms(*(ends[m].GetIdx() for m in edits[0]["atomMaps"]))
        bond.SetStereo(Chem.BondStereo.STEREONONE)
        for a in (bond.GetBeginAtom(), bond.GetEndAtom()):
            for b in a.GetBonds(): b.SetBondDir(Chem.BondDir.NONE)
        compatibility.validate_edit_contract(before, unsigned, edits, expected_fragments=1)


def equivalent_sites(molecule, first, second):
    heavy = [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    work = Chem.RemoveHs(Chem.Mol(molecule))
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    a, b = [tuple(heavy.index(i) for i in s[:2]) for s in (first, second)]
    return any({match[a[0]], match[a[1]]} == set(b) for match in work.GetSubstructMatches(work, uniquify=False, useChirality=True, maxMatches=512))


def metadata(substrate, reagents, site, report, *, anti_model=False):
    p = participants(substrate, reagents, site)
    return {"version": 1, **p, "selectedBondProductOrder": 3 - site[2],
            "stereoAssignment": "E" if site[2] == 1 and p["halogen"] == "Br" and anti_model else None,
            "geometryBasis": "qualified anti Br/Br; independently CIP-reassigned" if site[2] == 1 and p["halogen"] == "Br" and anti_model else
                             "first-stage halogen/medium stereospecificity unresolved" if site[2] == 1 else "saturated; no E/Z or new local stereocenters",
            "singleSiteBookkeepingOnly": report["singleSiteBookkeepingOnly"],
            "oxygenCompatibilityUnresolvedForCl2": report["oxygenCompatibilityUnresolvedForCl2"] and p["halogen"] == "Cl",
            "mechanism": "net only; complete halonium intermediate not implemented", "ratios": None,
            "note": "Selected one/two-X2 net graph, not experimental stopping or site selectivity. First-stage Br anti geometry requires the explicit compatible-medium model, not guaranteed exclusive E; incomplete settings stay unsigned. Cl2 geometry remains unsigned. Distant physical configurations and CIP are independently checked."}
