"""Bounded peroxyacid epoxidation with concerted atom provenance and syn stereo."""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo, epoxidation_stereo as geometry
    from .bromination_rule import equivalent_sites
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo, epoxidation_stereo as geometry
    from bromination_rule import equivalent_sites

SOURCE = "https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation"

def peroxyacid_sites(molecule):
    """Return (acyl C, carbonyl O, proximal O, terminal O), not peroxide OOH."""
    sites = []
    for c, carbonyl in graph.find_carbonyls(molecule):
        carbon = molecule.GetAtomWithIdx(c)
        for proximal in carbon.GetNeighbors():
            if proximal.GetSymbol() != "O" or proximal.GetIdx() == carbonyl or proximal.GetFormalCharge():
                continue
            if molecule.GetBondBetweenAtoms(c, proximal.GetIdx()).GetBondType() != Chem.BondType.SINGLE:
                continue
            neighbors = [a for a in proximal.GetNeighbors() if a.GetAtomicNum() != 1]
            if len(neighbors) != 2 or graph.attached_hydrogens(proximal):
                continue
            terminal = next((a for a in neighbors if a.GetIdx() != c), None)
            if terminal is None or terminal.GetSymbol() != "O" or terminal.GetFormalCharge():
                continue
            if (graph.attached_hydrogens(terminal) != 1
                    or len([a for a in terminal.GetNeighbors() if a.GetAtomicNum() != 1]) != 1
                    or molecule.GetBondBetweenAtoms(proximal.GetIdx(), terminal.GetIdx()).GetBondType() != Chem.BondType.SINGLE):
                continue
            if all(a.GetIdx() in {carbonyl, proximal.GetIdx()} or a.GetSymbol() in {"C", "H"} for a in carbon.GetNeighbors()):
                sites.append((c, carbonyl, proximal.GetIdx(), terminal.GetIdx()))
    return sites



def input_stereo_issue(smiles, normalized):
    """Inspect reagent annotations before canonicalization can erase them.

    This unsanitized copy never supplies chemistry or products. The selected
    model has no configured/chiral peroxyacid reagent scope, including tags
    that RDKit would clean off a non-stereogenic atom or carbonyl bond.
    """
    parser=Chem.SmilesParserParams();parser.sanitize=False;parser.removeHs=False
    raw=Chem.MolFromSmiles(smiles,parser)
    if (raw is None or raw.GetStereoGroups()
            or any(a.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED for a in raw.GetAtoms())
            or any(b.GetBondDir()!=Chem.BondDir.NONE or b.GetStereo()!=Chem.BondStereo.STEREONONE for b in raw.GetBonds())):
        return "Epoxidation peroxyacid reagent stereochemical annotations are not supported; no invalid or enhanced configuration is silently removed. Use a validated unconfigured peroxyacid structure."
    return None


def reagent_check(reagent):
    sites = peroxyacid_sites(reagent)
    if len(sites) != 1 or len(Chem.GetMolFrags(reagent)) != 1:
        raise ValueError("Epoxidation requires one actual connected peroxyacid R–C(=O)–O–O–H, not peroxide, perester, acid or multiple peracid sites.")
    if (any(a.GetSymbol() not in {"C", "H", "O", "Cl"} or a.GetFormalCharge() or a.GetNumRadicalElectrons()
            or a.GetIsotope() or a.HasQuery() or a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in reagent.GetAtoms())
            or any(b.GetStereo() != Chem.BondStereo.STEREONONE for b in reagent.GetBonds())
            or reagent.GetStereoGroups()):
        raise ValueError("The peroxyacid model needs a neutral specific closed-shell reagent without specified/relative stereo, isotopes or unvalidated elements.")
    acyl, carbonyl, proximal, terminal = sites[0]
    oxygens = {a.GetIdx() for a in reagent.GetAtoms() if a.GetAtomicNum() == 8}
    if oxygens != {carbonyl, proximal, terminal}:
        raise ValueError("Additional peroxyacid functional groups could undergo competing oxidation; only a screened ordinary alkyl/phenyl acyl skeleton is validated.")
    for atom in reagent.GetAtoms():
        if atom.GetAtomicNum() == 17 and (atom.GetDegree() != 1 or not atom.GetNeighbors()[0].GetIsAromatic()):
            raise ValueError("Only unactivated chlorophenyl substitution, including mCPBA, is screened for this peroxyacid model.")
    for bond in reagent.GetBonds():
        if bond.GetBondType() not in {Chem.BondType.SINGLE, Chem.BondType.AROMATIC} and set((bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())) != {acyl, carbonyl}:
            raise ValueError("Unsaturated or additional reducible/oxidizable peroxyacid substituents need separate reagent validation.")
    if any(len(r) < 5 or (any(reagent.GetAtomWithIdx(i).GetIsAromatic() for i in r) and
                         (len(r) != 6 or any(reagent.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in r)))
           for r in reagent.GetRingInfo().AtomRings()):
        raise ValueError("Strained/heteroaromatic peroxyacid reagent rings are not validated.")
    if Chem.AddHs(reagent).GetNumAtoms() > 80:
        raise ValueError("The peroxyacid exceeds the 80-explicit-atom reagent limit.")


def site_check(molecule, ends):
    if tuple(ends) not in graph.find_alkenes(molecule) and tuple(reversed(ends)) not in graph.find_alkenes(molecule):
        return "Choose an actual non-aromatic C=C for peroxyacid oxygen transfer."
    bond, rings = molecule.GetBondBetweenAtoms(*ends), molecule.GetRingInfo().AtomRings()
    if bond.IsInRing():
        selected = [r for r in rings if set(ends) <= set(r)]
        if (len(selected) != 1 or not 5 <= len(selected[0]) <= 7
                or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or sum(i in r for r in rings) != 1 for i in selected[0])):
            return "Cyclic epoxidation is screened only for isolated 5–7-membered carbocycles; other ring sizes, fused/bridged and heterocyclic environments need independent geometry validation."
    elif any(molecule.GetAtomWithIdx(i).IsInRing() for i in ends):
        return "Exocyclic/ring-junction epoxidation geometry is not independently validated."
    for i in ends:
        for neighbor in molecule.GetAtomWithIdx(i).GetNeighbors():
            if neighbor.GetIdx() in ends: continue
            if neighbor.GetAtomicNum() not in {1, 6}:
                return "Direct heteroatom-substituted/enol alkenes require separate peracid oxidation and epoxide-stability validation."
            if not neighbor.GetIsAromatic() and any(b.GetBondType() != Chem.BondType.SINGLE for b in neighbor.GetBonds()):
                return "Conjugated/cumulated or adjacent unsaturated epoxidation environments require additional chemoselectivity rules."
    return None


def group_check(molecule, ends, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkene":
        if set(indices) == set(ends):
            return "reactive", "validated", "The actual terminal peroxyacid oxygen closes the selected C=C into a three-membered epoxide."
        issue = site_check(molecule, tuple(indices))
        if issue: return "rejected", "competition", "Another C=C is not screened: " + issue
        return "alternative-site", "bounded", "An isolated unselected C=C remains in this one-oxygen-transfer net option. No free halonium/carbocation pi-capture permission is imported; further oxidation and experimental site selectivity are not predicted."
    if kind in {"alcohol", "ether"}:
        oxygens = [molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8]
        if len(oxygens) != 1: return "rejected", "unvalidated", "Unclassified oxygen is not a validated peracid spectator."
        oxygen = oxygens[0]
        carbons = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6]
        if not carbons or any(n.GetIsAromatic() or n.GetHybridization() != Chem.HybridizationType.SP3
                or graph.substitution_degree(n) >= 3 or graph.is_allylic_or_benzylic(n)
                or sum(a.GetAtomicNum() == 8 for a in n.GetNeighbors()) != 1 for n in carbons):
            return "rejected", "competition", "Activated/tertiary alcohols, enol/aryl/benzylic or acid-labile ethers and acetals are not inert peracid spectators."
        for other in graph.find_alkenes(molecule):
            for carbon in other:
                size = len(Chem.GetShortestPath(molecule, oxygen.GetIdx(), carbon))
                if size <= 8:
                    return "rejected", "competition", f"Nearby O atom {oxygen.GetIdx()+1} can direct oxidation or capture/open an epoxide through a potential {size}-membered ring; no isolated epoxide/facial outcome is established."
        return "preserved", "bounded", "Remote ordinary saturated OH/ether connectivity is retained only in the no-added-activation dry peracid net model. Acid coproduct, longer-range capture, later ring opening and actual chemoselectivity remain unpredicted."
    if kind == "aromatic ring":
        rings = molecule.GetRingInfo().AtomRings()
        if (len(indices) != 6 or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or sum(i in r for r in rings) != 1 for i in indices)
                or any(n.GetAtomicNum() not in {1, 6} for i in indices for n in molecule.GetAtomWithIdx(i).GetNeighbors())):
            return "rejected", "competition", "Activated, heteroatom-substituted or fused aromatic oxidation is not a screened spectator environment."
        return "preserved", "bounded", "An unactivated phenyl skeleton, including an aryl-adjacent alkene substituent, is retained in the concerted net model; subsequent styrene-oxide rearrangement/polymerization is not predicted."
    return "rejected", "competition", f"Additional {kind} has no validated peroxyacid compatibility policy; competing oxidation, acid sensitivity and ring opening are not assumed absent."


def extra_check(molecule, ends):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i))-1 if atom.GetIdx()!=i else 0 for i in ends)
            if distance < 2:
                yield "near-site-stereo", "unvalidated", "Adjacent specified centers require separate directed/diastereofacial epoxidation validation; their configurations are not discarded.", [atom.GetIdx()]


POLICY = compatibility.SitePolicy("selected-site peroxyacid epoxidation", frozenset({"C", "H", "O"}), site_check, group_check, extra_check, added_atoms=1)


def assess(molecule, site):
    return compatibility.assess_site(molecule, site[:2], POLICY)


def participants(substrate, reagent, site):
    reagent_check(reagent)
    acyl, carbonyl, proximal, terminal = peroxyacid_sites(reagent)[0]
    hydrogens = [a for a in reagent.GetAtomWithIdx(terminal).GetNeighbors() if a.GetAtomicNum() == 1]
    if len(hydrogens) != 1: raise ValueError("Concerted mapping requires the actual explicit peroxyacid O–H hydrogen.")
    return {"alkene": [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]],
            "acylCarbon": reagent.GetAtomWithIdx(acyl).GetAtomMapNum(),
            "carbonylOxygen": reagent.GetAtomWithIdx(carbonyl).GetAtomMapNum(),
            "proximalOxygen": reagent.GetAtomWithIdx(proximal).GetAtomMapNum(),
            "transferredOxygen": reagent.GetAtomWithIdx(terminal).GetAtomMapNum(),
            "peracidHydrogen": hydrogens[0].GetAtomMapNum()}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, reagent, site)
    return [{"atomMaps": p["alkene"], "before": 2., "after": 1.},
            {"atomMaps": [p["proximalOxygen"], p["transferredOxygen"]], "before": 1., "after": None},
            {"atomMaps": [p["transferredOxygen"], p["peracidHydrogen"]], "before": 1., "after": None},
            *[{"atomMaps": [c, p["transferredOxygen"]], "before": None, "after": 1.} for c in p["alkene"]],
            {"atomMaps": [p["acylCarbon"], p["proximalOxygen"]], "before": 1., "after": 2.},
            {"atomMaps": [p["acylCarbon"], p["carbonylOxygen"]], "before": 2., "after": 1.},
            {"atomMaps": [p["carbonylOxygen"], p["peracidHydrogen"]], "before": None, "after": 1.}]


def net_edit(editor, substrate, reagent, site):
    indexed = {a.GetAtomMapNum(): a.GetIdx() for a in editor.GetAtoms()}
    for change in edit_contract(substrate, reagent, site):
        a,b = [indexed[m] for m in change["atomMaps"]]
        if change["after"] is None: editor.RemoveBond(a,b)
        elif change["before"] is None: editor.AddBond(a,b,Chem.BondType.SINGLE)
        else:
            bond = editor.GetBondBetweenAtoms(a,b)
            bond.SetBondType(Chem.BondType.SINGLE if change["after"] == 1 else Chem.BondType.DOUBLE)
            bond.SetStereo(Chem.BondStereo.STEREONONE)
    Chem.SetDoubleBondNeighborDirections(editor)
    Chem.SanitizeMol(editor)


def variants(molecule, ends):
    substrate = Chem.AddHs(Chem.Mol(molecule))
    for a in substrate.GetAtoms(): a.SetAtomMapNum(a.GetIdx()+1)
    reagent = Chem.AddHs(Chem.MolFromSmiles("CC(=O)OO"))
    for a in reagent.GetAtoms(): a.SetAtomMapNum(substrate.GetNumAtoms()+a.GetIdx()+1)
    editor = Chem.RWMol(Chem.CombineMols(substrate,reagent))
    net_edit(editor,substrate,reagent,ends)
    _,_,_,centers,assigned = geometry.specification(substrate,editor,participants(substrate,reagent,ends))
    return [0,1] if centers and assigned else [0]


def sites(molecule):
    result = []
    for ends in graph.find_alkenes(molecule):
        report = assess(molecule,ends)
        result.extend((*ends,face) for face in (variants(molecule,ends) if report["eligible"] else [0]))
    return result


def candidates(substrate, reagent):
    try: reagent_check(reagent)
    except ValueError as exc: return [], [str(exc)]
    accepted, notes = [], []
    for site in sites(substrate):
        report = assess(substrate,site)
        if report["eligible"]: accepted.append(site)
        else: notes.extend(r["message"] for r in report["rejections"])
    return accepted, list(dict.fromkeys(notes))


def edit(editor, combined, substrate, reagent, site):
    if len(site) != 3 or type(site[2]) is not int or site[2] not in variants(substrate,site[:2]):
        raise ValueError("Choose a validated peroxyacid site/face alternative.")
    net_edit(editor,substrate,reagent,site)
    geometry.apply(substrate,editor,participants(substrate,reagent,site),site[2])


def validate(before, after, substrate, reagent, site):
    report = assess(substrate,site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    if len(site) != 3 or type(site[2]) is not int or site[2] not in variants(substrate,site[:2]):
        raise ValueError("Invalid epoxidation site/face alternative.")
    p = participants(substrate,reagent,site)
    geometry.validate(substrate,after,p,site[2])
    compatibility.validate_edit_contract(before,geometry.projected_product(after,p),edit_contract(substrate,reagent,site),
                                        consumed_double_bonds=[p["alkene"]],expected_fragments=2)
    parser=Chem.SmilesParserParams(); parser.removeHs=False
    restored=Chem.MolFromSmiles(Chem.MolToSmiles(after),parser)
    if restored is None: raise ValueError("The configured epoxide/acid products did not serialize.")
    geometry.validate(substrate,restored,p,site[2])


def stereo_metadata(substrate, product, reagent, site):
    p=participants(substrate,reagent,site)
    refs,same,basis,centers,assigned=geometry.specification(substrate,product,p)
    return {"additionGeometry":"syn oxygen transfer", "basis":basis,
            "outcome":"validated same-face alternative" if assigned else "no local stereocenters" if not centers else "unassigned: starting alkene geometry unknown",
            "assignedAtomMaps":sorted(centers) if assigned else [], "referenceMaps":[r[0] for r in refs],
            "referenceSameSide":same, "productReferenceRelationship":None if same is None else "cis" if same else "trans",
            "faceAlternative":site[2] if assigned else None, "ratios":None,
            "note":"Cis/trans refers to the two named mapped substituents, not to every group or a facial population. One oxygen bridges the same alkene face. Unknown geometry stays unsigned; distant configurations/CIP are checked; no selective mono-epoxidation or isolated yield is predicted."}


def context_issue(conditions):
    if conditions.get("catalyst") == "radical":
        return "Radical activation is not the supported concerted peroxyacid oxygen-transfer model; no epoxide is inferred from a radical setting."
    return None
