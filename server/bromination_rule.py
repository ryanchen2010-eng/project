"""Bounded Br2 net addition and stereospecific anti alternatives, not a protocol."""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo, bromination_stereo as anti
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo, bromination_stereo as anti

SOURCE = "https://openstax.org/books/organic-chemistry/pages/8-2-halogenation-of-alkenes-addition-of-x2"


def reagent_check(reagent):
    if (reagent.GetNumAtoms() != 2 or reagent.GetNumBonds() != 1
            or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or any(a.GetAtomicNum() != 35 or a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons()
                   or a.HasQuery() or graph.attached_hydrogens(a) for a in reagent.GetAtoms())):
        raise ValueError("Alkene bromination requires actual neutral Br–Br, not HBr, bromide, NBS, mixed halogens or another X2 reagent.")


def site_check(molecule, ends):
    if tuple(ends) not in graph.find_alkenes(molecule) and tuple(reversed(ends)) not in graph.find_alkenes(molecule):
        return "Select an actual non-aromatic C=C for Br2 addition."
    bond, rings = molecule.GetBondBetweenAtoms(*ends), molecule.GetRingInfo().AtomRings()
    if bond.IsInRing():
        selected = [r for r in rings if set(ends) <= set(r)]
        if (len(selected) != 1 or not 5 <= len(selected[0]) <= 8
                or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or sum(i in r for r in rings) != 1 for i in selected[0])):
            return "Bromination ring geometry is screened only for isolated 5–8-membered carbocycles; small/large, fused, bridged or heterocyclic sites need separate validation."
    elif any(molecule.GetAtomWithIdx(i).IsInRing() for i in ends):
        return "Exocyclic/ring-junction bromination geometry is not independently validated."
    aromatic_ends = []
    for index in ends:
        for neighbor in molecule.GetAtomWithIdx(index).GetNeighbors():
            if neighbor.GetIdx() in ends: continue
            if neighbor.GetAtomicNum() not in {1, 6}:
                return "Direct heteroatom-substituted/enol alkenes need separate bromination/protonation and capture rules."
            if neighbor.GetIsAromatic(): aromatic_ends.append(index)
            elif any(b.GetBondType() != Chem.BondType.SINGLE for b in neighbor.GetBonds()):
                return "Conjugated/cumulated and adjacent unsaturated bromination pathways are not this isolated-site model."
    if aromatic_ends:
        # Benzylic opening can lose stereospecificity. Terminal styrenes have
        # at most one new center, so no internal anti pair is falsely assigned.
        if len(aromatic_ends) != 1 or not any(graph.attached_hydrogens(molecule.GetAtomWithIdx(i)) == 2 for i in ends):
            return "Internal/multiply aryl-adjacent alkenes can have open benzylic-ion stereo scrambling; stereospecific dibromination is not validated for this environment."
    return None


def group_check(molecule, ends, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkene":
        if set(indices) == set(ends):
            return "reactive", "validated", "Actual Br2 supplies one bromine to each selected alkene carbon."
        issue = site_check(molecule, tuple(indices))
        if issue: return "rejected", "competition", "Another alkene is not screened: " + issue
        if any(len(Chem.GetShortestPath(molecule, a, b)) <= 8 for a in ends for b in indices):
            return "rejected", "competition", "A nearby second C=C may capture the bromonium/involve cyclization; selective one-site dibromination is unresolved, not chemically impossible."
        return "alternative-site", "bounded", "A sufficiently separated screened C=C remains an independent net site. Further bromination, larger-ring/intermolecular capture and experimental one-site selectivity are not predicted."
    if kind in {"alcohol", "ether"}:
        oxygens = [molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8]
        if len(oxygens) != 1: return "rejected", "unvalidated", "This oxygen environment is not a screened Br2 spectator."
        oxygen = oxygens[0]
        carbons = [a for a in oxygen.GetNeighbors() if a.GetAtomicNum() == 6]
        if (not carbons or any(a.GetIsAromatic() or a.GetHybridization() != Chem.HybridizationType.SP3
                or graph.substitution_degree(a) >= 3 or graph.is_allylic_or_benzylic(a)
                or sum(n.GetAtomicNum() == 8 for n in a.GetNeighbors()) != 1 for a in carbons)):
            return "rejected", "competition", "Only remote saturated primary/secondary alcohols and ordinary dialkyl ethers have a bounded Br2 spectator scope; phenols/enol ethers, activated/tertiary oxygen and acetal environments are excluded."
        for site in graph.find_alkenes(molecule):
            for carbon in site:
                size = len(Chem.GetShortestPath(molecule, oxygen.GetIdx(), carbon))
                if size <= 8:
                    return "rejected", "competition", f"Potential {size}-membered intramolecular oxygen capture/cyclization at O atom {oxygen.GetIdx()+1} competes with bromide opening. No dibromide-only product is assigned."
        return "preserved", "bounded", "Remote ordinary oxygen connectivity is retained only in the neutral non-nucleophilic, no-added-activation Br2 net model. Protonation, oxidation/cleavage, larger-ring capture and actual chemoselectivity are not established."
    if kind == "aromatic ring":
        rings = molecule.GetRingInfo().AtomRings()
        if (len(indices) != 6 or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or sum(i in r for r in rings) != 1 for i in indices)
                or any(n.GetAtomicNum() not in {1, 6} for i in indices for n in molecule.GetAtomWithIdx(i).GetNeighbors())):
            return "rejected", "competition", "Activated/hetero/fused aromatic bromination is not screened as an inert ring."
        return "preserved", "bounded", "An unactivated isolated phenyl skeleton is retained without a Lewis-acid/radical activation claim. Aromatic substitution, benzylic radical bromination and styrene polymerization are not predicted."
    return "rejected", "competition", f"Additional {kind} has no validated Br2 compatibility policy; competing oxidation, substitution or capture is not assumed absent."


def extra_check(molecule, ends):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i))-1 if atom.GetIdx()!=i else 0 for i in ends)
            if distance < 2:
                yield "near-site-stereo", "unvalidated", "Adjacent specified stereocenters need a separately validated bromination facial/neighboring-participation model; no configuration is discarded.", [atom.GetIdx()]


POLICY = compatibility.SitePolicy("selected-site Br2 addition", frozenset({"C", "H", "O"}), site_check, group_check, extra_check, added_atoms=2)


def assess(molecule, site):
    return compatibility.assess_site(molecule, site[:2], POLICY)


def participants(substrate, reagent, site):
    reagent_check(reagent)
    return {"alkene": [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]],
            "bromines": [a.GetAtomMapNum() for a in reagent.GetAtoms()]}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, reagent, site)
    return [{"atomMaps": p["alkene"], "before": 2.0, "after": 1.0},
            {"atomMaps": p["bromines"], "before": 1.0, "after": None},
            *[{"atomMaps": [c, br], "before": None, "after": 1.0} for c, br in zip(p["alkene"], p["bromines"])]]


def net_edit(editor, substrate, reagent, site):
    indexed = {a.GetAtomMapNum(): a.GetIdx() for a in editor.GetAtoms()}
    for change in edit_contract(substrate, reagent, site):
        a,b = [indexed[m] for m in change["atomMaps"]]
        if change["after"] is None: editor.RemoveBond(a,b)
        elif change["before"] is None: editor.AddBond(a,b,Chem.BondType.SINGLE)
        else:
            bond = editor.GetBondBetweenAtoms(a,b)
            bond.SetBondType(Chem.BondType.SINGLE); bond.SetStereo(Chem.BondStereo.STEREONONE)
    Chem.SetDoubleBondNeighborDirections(editor)
    Chem.SanitizeMol(editor)


def variants(molecule, ends):
    substrate = Chem.AddHs(Chem.Mol(molecule))
    for a in substrate.GetAtoms(): a.SetAtomMapNum(a.GetIdx()+1)
    reagent = Chem.MolFromSmiles("BrBr")
    for a in reagent.GetAtoms(): a.SetAtomMapNum(substrate.GetNumAtoms()+a.GetIdx()+1)
    editor = Chem.RWMol(Chem.CombineMols(substrate,reagent))
    net_edit(editor,substrate,reagent,ends)
    _,_,_,centers,assigned = anti.specification(substrate,editor,participants(substrate,reagent,ends))
    return [0,1] if centers and assigned else [0]


def sites(molecule):
    result = []
    for ends in graph.find_alkenes(molecule):
        report = assess(molecule,ends)
        result.extend((*ends,face) for face in (variants(molecule,ends) if report["eligible"] else [0]))
    return result


def edit(editor, substrate, reagent, site):
    if len(site)!=3 or type(site[2]) is not int or site[2] not in variants(substrate,site[:2]):
        raise ValueError("Choose a validated Br2 site and opposite-face alternative.")
    net_edit(editor,substrate,reagent,site)
    anti.apply(substrate,editor,participants(substrate,reagent,site),site[2])


def validate(before, after, substrate, reagent, site):
    report = assess(substrate,site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    if len(site)!=3 or type(site[2]) is not int or site[2] not in variants(substrate,site[:2]):
        raise ValueError("Invalid Br2 stereochemical alternative.")
    p = participants(substrate,reagent,site)
    anti.validate(substrate,after,p,site[2])
    # Validate unchanged spectator stereo with only the separately authorized
    # new local tags projected out. The shared validator itself is unchanged.
    compatibility.validate_edit_contract(before,anti.projected_product(after,p),edit_contract(substrate,reagent,site),
                                        consumed_double_bonds=[p["alkene"]],expected_fragments=1)
    parser=Chem.SmilesParserParams(); parser.removeHs=False
    restored=Chem.MolFromSmiles(Chem.MolToSmiles(after),parser)
    if restored is None: raise ValueError("The stereochemical Br2 product did not serialize.")
    anti.validate(substrate,restored,p,site[2])


def stereo_metadata(substrate, product, reagent, site):
    p=participants(substrate,reagent,site)
    refs,same,basis,centers,assigned=anti.specification(substrate,product,p)
    bond=substrate.GetBondBetweenAtoms(*site[:2])
    return {"additionGeometry":"anti", "basis":basis,
            "outcome":"validated opposite-face alternative" if assigned else "no local stereocenters" if not centers else "unassigned: starting alkene geometry unknown",
            "assignedAtomMaps":sorted(centers) if assigned else [],"referenceMaps":[r[0] for r in refs],
            "referenceSameSide":same, "faceAlternative":site[2] if assigned else None,
            # Do not label every anti product trans, especially large rings.
            "productRingRelationship":"trans Br/Br" if bond.IsInRing() and assigned
                and any(5 <= len(r) <= 7 and set(site[:2]) <= set(r) for r in substrate.GetRingInfo().AtomRings()) else None,
            "ratios":None,"note":"Opposite approach faces, not a random conformer. Anti describes addition geometry; acyclic products are not generically called trans. No populations or selective mono-conversion predicted."}


def equivalent_sites(molecule, first, second):
    heavy=[a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum()!=1]
    work=Chem.RemoveHs(Chem.Mol(molecule))
    for a in work.GetAtoms(): a.SetAtomMapNum(0)
    a,b=[tuple(heavy.index(i) for i in s[:2]) for s in (first,second)]
    return any({m[a[0]],m[a[1]]}==set(b) for m in work.GetSubstructMatches(work,uniquify=False,useChirality=True,maxMatches=512))


def context_issue(conditions):
    if conditions.get("catalyst")=="radical":
        return "Radical Br2/allylic substitution is not the supported bromonium anti-addition model; no ionic dibromide is inferred under radical activation."
    return None
