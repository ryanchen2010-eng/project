"""Bounded catalytic Os/H2O2 syn diol NET model, not an osmium mechanism.

H2O2 supplies the formal net atom inventory. Oxygen cycling through omitted
osmium species and proton exchange during aqueous release are NOT traced.
No NMO, permanganate, cleavage or asymmetric ligand model is introduced.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
    from .bromination_stereo import references, local_centers, normalized_tag, set_tag, projected_product
    from .bromination_rule import equivalent_sites
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
    from bromination_stereo import references, local_centers, normalized_tag, set_tag, projected_product
    from bromination_rule import equivalent_sites

SOURCE = "https://www.orgsyn.org/demo.aspx?prep=CV6P0342"
LIMITATION = ("Balanced explicit-species net model only: H2O2 supplies formal O/H bookkeeping, not elementary oxygen/proton provenance. "
              "Os catalyst cycling, cyclic osmate, aqueous release species, proton exchange and further oxidation are omitted. "
              "No complete mapped mechanism, experimental conversion, facial preference or selective mono-dihydroxylation is predicted.")


def input_reagent_issue(smiles):
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if (raw is None or raw.GetStereoGroups() or any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in raw.GetAtoms())
            or any(b.GetBondDir() != Chem.BondDir.NONE or b.GetStereo() != Chem.BondStereo.STEREONONE for b in raw.GetBonds())):
        return "Dihydroxylation H2O2 has no configured stereochemical reagent model; invalid or enhanced annotations are not silently removed."
    return None


def reagent_check(molecule):
    heavy = [a for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    if (len(heavy) != 2 or any(a.GetAtomicNum() != 8 or a.GetFormalCharge() or a.GetNumRadicalElectrons()
            or a.GetIsotope() or a.HasQuery() or a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
            or graph.attached_hydrogens(a) != 1 for a in heavy)
            or len(Chem.GetMolFrags(molecule)) != 1
            or molecule.GetBondBetweenAtoms(heavy[0].GetIdx(), heavy[1].GetIdx()) is None
            or molecule.GetBondBetweenAtoms(heavy[0].GetIdx(), heavy[1].GetIdx()).GetBondType() != Chem.BondType.SINGLE):
        raise ValueError("This dihydroxylation model requires actual neutral H2O2 with Os activation; other peroxides, NMO and permanganate are not enabled.")


def site_check(molecule, ends):
    if frozenset(ends) not in {frozenset(s) for s in graph.find_alkenes(molecule)}:
        return "Dihydroxylation requires an actual non-aromatic C=C."
    bond, rings = molecule.GetBondBetweenAtoms(*ends), molecule.GetRingInfo().AtomRings()
    if bond.IsInRing():
        selected = [r for r in rings if set(ends) <= set(r)]
        if (len(selected) != 1 or not 5 <= len(selected[0]) <= 7 or any(
                molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or sum(i in r for r in rings) != 1 for i in selected[0])):
            return "Syn dihydroxylation ring geometry is validated only for isolated 5–7-membered carbocycles, not fused/bridged, heterocyclic or larger rings."
    elif any(molecule.GetAtomWithIdx(i).IsInRing() for i in ends):
        return "Exocyclic/ring-junction dihydroxylation stereochemistry needs separate validation."
    for i in ends:
        for n in molecule.GetAtomWithIdx(i).GetNeighbors():
            if n.GetIdx() in ends: continue
            if n.GetAtomicNum() not in {1, 6}:
                return "Direct heteroatom/enol alkene substitution needs separate oxidation validation."
            if not n.GetIsAromatic() and any(b.GetBondType() != Chem.BondType.SINGLE for b in n.GetBonds()):
                return "Conjugated/cumulated or adjacent unsaturated dihydroxylation chemistry is not validated."
    return None


def group_check(molecule, ends, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkene":
        if set(indices) == set(ends):
            return "reactive", "validated", "Selected C=C receives two same-face OH groups in the formal Os/H2O2 net model."
        issue = site_check(molecule, tuple(indices))
        if issue: return "rejected", "competition", "Unselected C=C is not screened: " + issue
        distance = min(len(Chem.GetShortestPath(molecule, a, b))-1 for a in ends for b in indices)
        if distance <= 4:
            return "rejected", "competition", "Nearby diene oxidation/cyclic osmate capture needs separate oxidative-cyclization validation; no selective diol is inferred."
        return "alternative-site", "bounded", "Isolated distant C=C retained in a one-site net option; further oxidation and experimental site selectivity are not predicted."
    if kind in {"alcohol", "ether"}:
        oxygen = next(molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8)
        carbons = [a for a in oxygen.GetNeighbors() if a.GetAtomicNum() == 6]
        if not carbons or any(a.GetIsAromatic() or a.GetHybridization() != Chem.HybridizationType.SP3
                or graph.substitution_degree(a) >= 3 or graph.is_allylic_or_benzylic(a)
                or sum(n.GetAtomicNum() == 8 for n in a.GetNeighbors()) != 1 for a in carbons):
            return "rejected", "competition", "Activated/tertiary/benzylic alcohols, aryl/enol or acid-sensitive ethers and acetals are not validated oxidation spectators."
        distance = min(len(Chem.GetShortestPath(molecule, oxygen.GetIdx(), i))-1 for s in graph.find_alkenes(molecule) for i in s)
        if distance < 4:
            return "rejected", "competition", "Near-site OH/ether coordination, directed osmylation and competing capture need independent validation; facial selectivity is not assumed."
        return "preserved", "bounded", "Screened remote saturated OH/ether retained in the net graph; coordination, peroxide side oxidation and actual chemoselectivity are not predicted."
    if kind == "aromatic ring":
        rings = molecule.GetRingInfo().AtomRings()
        if (len(indices) != 6 or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or sum(i in r for r in rings) != 1 for i in indices)
                or any(n.GetAtomicNum() not in {1, 6} for i in indices for n in molecule.GetAtomWithIdx(i).GetNeighbors())):
            return "rejected", "competition", "Activated/heteroatom-substituted or fused aromatic oxidation requires separate validation."
        return "preserved", "bounded", "Unactivated phenyl, including styrene-type adjacency, retained under the bounded syn net model; no universal aromatic inertness is asserted."
    return "rejected", "competition", f"Additional {kind} has no validated Os/H2O2 compatibility policy; competing oxidation is not assumed absent."


def extra_check(molecule, ends):
    for a in molecule.GetAtoms():
        if a.GetChiralTag() in stereo.TETRAHEDRAL and min(len(Chem.GetShortestPath(molecule, a.GetIdx(), i))-1 for i in ends) < 2:
            yield "near-site-stereo", "unvalidated", "Adjacent specified stereocenters require directed/diastereofacial osmylation validation; configurations are not discarded.", [a.GetIdx()]


POLICY = compatibility.SitePolicy("selected-site syn Os/H2O2 dihydroxylation", frozenset({"C", "H", "O"}), site_check, group_check, extra_check, added_atoms=4)


def assess(molecule, site): return compatibility.assess_site(molecule, site[:2], POLICY)


def participants(substrate, reagent, site):
    reagent_check(reagent)
    oxygens = [a for a in reagent.GetAtoms() if a.GetAtomicNum() == 8]
    hs = [[n.GetAtomMapNum() for n in a.GetNeighbors() if n.GetAtomicNum() == 1] for a in oxygens]
    if any(len(h) != 1 for h in hs): raise ValueError("The net H2O2 donor requires both explicit mapped O–H hydrogens.")
    return {"alkene": [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]],
            "oxygens": [a.GetAtomMapNum() for a in oxygens], "hydroxylHydrogens": [h[0] for h in hs],
            "provenanceModel": "formal net bookkeeping; not catalyst oxygen cycling or proton exchange"}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, reagent, site)
    return [{"atomMaps": p["alkene"], "before": 2., "after": 1.},
            {"atomMaps": p["oxygens"], "before": 1., "after": None},
            *[{"atomMaps": [c, o], "before": None, "after": 1.} for c, o in zip(p["alkene"], p["oxygens"])]]


def specification(substrate, product, p):
    ends = [next(a.GetIdx() for a in substrate.GetAtoms() if a.GetAtomMapNum() == m) for m in p["alkene"]]
    refs, same, basis = references(substrate, ends)
    centers = local_centers(product, p["alkene"])
    # A terminal/identical-substituent end cannot have E/Z. Its two possible
    # faces are explicit alternatives, not an assigned unknown E/Z geometry.
    assigned = bool(centers) and (same is not None or len(centers) == 1)
    return refs, same, basis, centers, assigned


def net_edit(editor, substrate, reagent, site):
    indexed = {a.GetAtomMapNum(): a.GetIdx() for a in editor.GetAtoms()}
    for change in edit_contract(substrate, reagent, site):
        a, b = [indexed[m] for m in change["atomMaps"]]
        if change["after"] is None: editor.RemoveBond(a, b)
        elif change["before"] is None: editor.AddBond(a, b, Chem.BondType.SINGLE)
        else:
            bond = editor.GetBondBetweenAtoms(a, b); bond.SetBondType(Chem.BondType.SINGLE)
            bond.SetStereo(Chem.BondStereo.STEREONONE)
    Chem.SetDoubleBondNeighborDirections(editor)
    Chem.SanitizeMol(editor)


def apply_stereo(substrate, editor, p, face):
    refs, same, _, centers, assigned = specification(substrate, editor, p)
    atoms = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    for i, number in enumerate(p["alkene"]):
        atoms[number].SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        if assigned and number in centers:
            # Exact reference order: same-face OH requires opposite local
            # parity iff ref0 groups lay on the same starting alkene side.
            value = bool(face) if i == 0 else bool(face) ^ (same is True)
            set_tag(atoms[number], [p["alkene"][1-i], *refs[i], p["oxygens"][i]], value)


def validate_stereo(substrate, product, p, face):
    refs, same, _, centers, assigned = specification(substrate, product, p)
    atoms = {a.GetAtomMapNum(): a for a in product.GetAtoms()}
    checked = {a.GetAtomMapNum(): a for a in stereo._checked_stereo(product).GetAtoms()}
    for i, number in enumerate(p["alkene"]):
        if assigned and number in centers:
            expected = bool(face) if i == 0 else bool(face) ^ (same is True)
            if normalized_tag(checked[number], [p["alkene"][1-i], *refs[i], p["oxygens"][i]]) != expected:
                raise ValueError("Diol configuration is not the validated same-face OH alternative.")
        elif atoms[number].GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED:
            raise ValueError("Dihydroxylation cannot invent configuration from unknown starting geometry or at a non-stereogenic center.")


def variants(molecule, ends):
    substrate = Chem.AddHs(Chem.Mol(molecule)); reagent = Chem.AddHs(Chem.MolFromSmiles("OO"))
    for a in substrate.GetAtoms(): a.SetAtomMapNum(a.GetIdx()+1)
    for a in reagent.GetAtoms(): a.SetAtomMapNum(substrate.GetNumAtoms()+a.GetIdx()+1)
    editor = Chem.RWMol(Chem.CombineMols(substrate, reagent)); net_edit(editor, substrate, reagent, ends)
    _, _, _, centers, assigned = specification(substrate, editor, participants(substrate, reagent, ends))
    return [0, 1] if centers and assigned else [0]


def sites(molecule):
    return [(*ends, face) for ends in graph.find_alkenes(molecule)
            for face in (variants(molecule, ends) if assess(molecule, ends)["eligible"] else [0])]


def edit(editor, combined, substrate, reagent, site):
    if len(site) != 3 or type(site[2]) is not int or site[2] not in variants(substrate, site[:2]):
        raise ValueError("Choose a validated dihydroxylation site/face alternative.")
    net_edit(editor, substrate, reagent, site)
    apply_stereo(substrate, editor, participants(substrate, reagent, site), site[2])


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    if len(site) != 3 or type(site[2]) is not int or site[2] not in variants(substrate, site[:2]):
        raise ValueError("Invalid dihydroxylation face/site.")
    p = participants(substrate, reagent, site); validate_stereo(substrate, after, p, site[2])
    compatibility.validate_edit_contract(before, projected_product(after, p), edit_contract(substrate, reagent, site),
                                        consumed_double_bonds=[p["alkene"]], expected_fragments=1)
    parser = Chem.SmilesParserParams(); parser.removeHs = False
    restored = Chem.MolFromSmiles(Chem.MolToSmiles(after), parser)
    if restored is None: raise ValueError("The syn diol could not be serialized.")
    validate_stereo(substrate, restored, p, site[2])


def stereo_metadata(substrate, product, reagent, site):
    p = participants(substrate, reagent, site)
    _, same, basis, centers, assigned = specification(substrate, product, p)
    cyclic = substrate.GetBondBetweenAtoms(*site[:2]).IsInRing()
    return {"additionGeometry": "syn OH/OH", "basis": basis,
            "outcome": "validated cis OH/OH" if assigned and cyclic else "validated same-face alternative" if assigned else "no local stereocenters" if not centers else "unassigned: starting alkene geometry unknown",
            "assignedAtomMaps": sorted(centers) if assigned else [], "faceAlternative": site[2] if assigned else None,
            "hydroxylRelationship": "cis" if assigned and cyclic else None, "referenceSameSide": same, "ratios": None,
            "note": "Syn refers to the two entering OH groups, not identical R/S letters. Meso/equivalent products are grouped; enantiomeric or diastereomeric alternatives have no predicted ratio. Unknown internal geometry stays unsigned; 3D is only a representative conformer. " + LIMITATION}
