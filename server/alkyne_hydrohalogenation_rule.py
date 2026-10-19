"""Selected-site ionic HX net accounting, not a vinyl-cation mechanism.

Terminal Markovnikov orientation and internal constitutional alternatives use
alkyne-specific rules. No E/Z, rates, face populations or experimental stopping
are inferred from generic HX selectors or a generated conformer.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

PATHWAY = "Alkyne hydrohalogenation"
SOURCE = "https://openstax.org/books/organic-chemistry/pages/9-3-reactions-of-alkynes-addition-of-hx-and-x2"
LIMITATION = ("Actual one/two HX equivalents give selected-site vinyl-halide/geminal-dihalide net equations. "
              "Internal regioisomers are alternatives without proportions; first-stage internal E/Z remains unassigned. "
              "HCl, HBr and HI have independent output gates; supply, stopping and competing chemistry are not established. "
              "No complete vinyl-cation, concerted elementary or radical mechanism is implemented.")


def input_stereo_issue(smiles, normalized):
    issue = stereo.stereo_scope_issue(normalized, "alkyne ionic HX addition")
    if issue: return issue
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None: return "Alkyne HX addition cannot validate the supplied stereochemical annotations."
    old = [a for a in raw.GetAtoms() if a.GetAtomicNum() != 1]
    new = [a for a in normalized.GetAtoms() if a.GetAtomicNum() != 1]
    if len(old) != len(new) or any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                                 and (a.GetChiralTag() not in stereo.TETRAHEDRAL or b.GetChiralTag() not in stereo.TETRAHEDRAL)
                                 for a, b in zip(old, new)):
        return "Invalid or nonstandard specified centers cannot be silently removed during alkyne HX normalization."
    if any(b.GetBondDir() != Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return "Directional annotations without C=C are unsupported; the starting alkyne has no assumed E/Z."
    return None


def hx_element(molecule):
    work = Chem.AddHs(Chem.Mol(molecule))
    atoms = list(work.GetAtoms())
    if (len(atoms) != 2 or work.GetNumBonds() != 1 or work.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or sorted(a.GetAtomicNum() for a in atoms)[0] != 1
            or sum(a.GetSymbol() in {"Cl", "Br", "I"} for a in atoms) != 1
            or any(a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery() for a in atoms)):
        raise ValueError("Use one actual neutral HCl, HBr or HI molecule per equivalent; HF, X2, salts, radicals and arbitrary donors are unsupported.")
    return next(a.GetSymbol() for a in atoms if a.GetAtomicNum() != 1)


def site_issue(molecule, ends):
    if tuple(ends) not in graph.find_alkynes(molecule) and tuple(reversed(ends)) not in graph.find_alkynes(molecule):
        return "Ionic alkyne HX addition requires an actual selected C≡C bond."
    if molecule.GetBondBetweenAtoms(*ends).IsInRing():
        return "Cyclic alkyne strain, addition geometry and ring rearrangements require independent validation."
    for i in ends:
        for n in molecule.GetAtomWithIdx(i).GetNeighbors():
            if n.GetIdx() in ends or n.GetAtomicNum() == 1: continue
            if n.GetAtomicNum() != 6 or n.GetIsAromatic() or n.GetHybridization() != Chem.HybridizationType.SP3:
                return "Conjugated, aromatic-adjacent or directly heteroatom-substituted alkyne HX chemistry needs a separate orientation/mechanism model."
            if graph.substitution_degree(n) >= 3 or n.IsInRing():
                return "Directly adjacent branched/quaternary or ring-bound environments need separate vinyl-ion/shift compatibility; an unrearranged HX outcome is not guaranteed."
    return None


def equivalent_choices(molecule, first, second):
    """Preserve a whole C≡C AND the halogen-target atom under a chiral symmetry."""
    heavy = [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    work = Chem.RemoveHs(Chem.Mol(molecule))
    for a in work.GetAtoms(): a.SetAtomMapNum(0)
    a, b = [tuple(heavy.index(i) for i in choice[:3]) for choice in (first, second)]
    return any({match[a[0]], match[a[1]]} == set(b[:2]) and match[a[2]] == b[2]
               for match in work.GetSubstructMatches(work, uniquify=False, useChirality=True, maxMatches=512))


def orientations(molecule, ends):
    hs = [graph.attached_hydrogens(molecule.GetAtomWithIdx(i)) for i in ends]
    if hs[0] != hs[1]:
        return [ends[hs.index(min(hs))]], "terminal Markovnikov net orientation: X at the carbon without the terminal H"
    if equivalent_choices(molecule, (*ends, ends[0]), (*ends, ends[1])):
        return [ends[0]], "whole-graph symmetry makes the two alkyne orientations equivalent"
    return list(ends), "inequivalent internal ends: both constitutional net alternatives, no preference or ratio established"


def sites(molecule, equivalents):
    for ends in graph.find_alkynes(molecule):
        targets, _ = orientations(molecule, ends)
        for target in targets: yield (*ends, target, equivalents)


def group_check(molecule, ends, group, symbol):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkyne":
        if set(indices) == set(ends): return "reactive", "validated", f"Selected C≡C receives the actual H{symbol} atom pairs; X2 and alkene cation rules are not substituted."
        if site_issue(molecule, indices) or group["distance"] < 4:
            return "rejected", "competition", "A nearby/conjugated or ring-bound additional alkyne has unresolved ionic HX capture/cyclization."
        return "alternative-site", "competition", "Another isolated C≡C can also consume HX; selective one-site conversion is unresolved, so this equation is conditional 2D bookkeeping only."
    if kind in {"alcohol", "ether"}:
        oxygen = next(molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8)
        size = min(len(Chem.GetShortestPath(molecule, oxygen.GetIdx(), i)) for i in ends)
        if size <= 6:
            return "rejected", "competition", f"Nearby {kind} oxygen permits a shortest potential {size}-membered intramolecular capture path; this ionic HX cyclization/protonation environment is unvalidated."
        carbons = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6]
        ordinary = (not oxygen.IsInRing() and len(carbons) == (1 if kind == "alcohol" else 2)
                    and all(c.GetHybridization() == Chem.HybridizationType.SP3 and not c.GetIsAromatic()
                            and not graph.is_allylic_or_benzylic(c) and sum(n.GetAtomicNum() == 8 for n in c.GetNeighbors()) == 1
                            and graph.substitution_degree(c) <= (1 if kind == "alcohol" else 2) for c in carbons))
        if not ordinary:
            return "rejected", "competition", "Secondary/tertiary alcohols, activated/cyclic ethers and acetal-like groups require separate HX substitution/cleavage validation."
        return "preserved", "conditional-only", f"Screened remote {kind} is retained only in a hypothetical selected-site H{symbol} equation. Protonation, substitution/ether cleavage remain unresolved; no O-preserving selective 3D outcome is asserted."
    if kind == "peroxide":
        return "rejected", "competition", "A peroxide can introduce radical HBr/other competing chemistry; no anti-Markovnikov radical model is enabled."
    return "rejected", "competition", f"Additional {kind} protonation, addition, hydrolysis or rearrangement is not a validated H{symbol} spectator."


def additional_check(molecule, ends):
    rings = molecule.GetRingInfo().AtomRings()
    if len(rings) > 1 or any(len(r) > 8 or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or
            molecule.GetAtomWithIdx(i).GetHybridization() != Chem.HybridizationType.SP3 for i in r) for r in rings):
        yield "complex-ring", "unvalidated", "Complex/heterocyclic/unsaturated ring HX chemistry needs independent validation.", sorted({i for r in rings for i in r})
    for a in molecule.GetAtoms():
        if a.GetChiralTag() in stereo.TETRAHEDRAL and min(len(Chem.GetShortestPath(molecule, a.GetIdx(), i))-1 if a.GetIdx()!=i else 0 for i in ends) < 2:
            yield "near-site-stereo", "unvalidated", "A specified propargylic center needs separate ionic HX shift/directed/epimerization validation; no tag is silently removed.", [a.GetIdx()]


def assess(molecule, reagent, site):
    if len(site) != 4 or site[2] not in site[:2] or type(site[3]) is not int or site[3] not in {1, 2}:
        raise ValueError("Choose a valid alkyne orientation and one/two HX equivalents.")
    symbol = hx_element(reagent)
    policy = compatibility.SitePolicy(f"isolated-alkyne ionic H{symbol} addition", frozenset({"C", "H", "O"}), site_issue,
                                      lambda m,s,g: group_check(m,s,g,symbol), additional_check, added_atoms=2*site[3])
    result = compatibility.assess_site(molecule, site[:2], policy)
    for rejection in result["rejections"]:
        if rejection["code"] == "product-size": rejection["message"] = f"The selected HX product exceeds 80 explicit atoms including {site[3]} incoming H and {site[3]} incoming halogen atoms."
    targets, basis = orientations(molecule, site[:2])
    if site[2] not in targets:
        result["rejections"].append({"code":"orientation", "category":"unvalidated", "message":"This target is not the bounded terminal Markovnikov/internal-alternative orientation.","atomIndices":[site[2]]})
        result["eligible"] = False
    result.update(hydrogenHalide="H"+symbol, orientationBasis=basis, orientationCount=len(targets),
                  internal=all(graph.attached_hydrogens(molecule.GetAtomWithIdx(i))==0 for i in site[:2]),
                  singleSiteBookkeepingOnly=any(g["type"]=="alkyne" and g["disposition"]=="alternative-site" for g in result["groups"]),
                  oxygenCompetition=any(g["type"] in {"alcohol","ether"} and g["disposition"]=="preserved" for g in result["groups"]))
    return result


def participants(substrate, reagents, site):
    if len(site)!=4 or site[2] not in site[:2] or type(site[3]) is not int or site[3] not in {1,2} or len(reagents)!=site[3]:
        raise ValueError("Exactly the selected number of actual HX molecules is required.")
    pairs, symbols = [], set()
    for reagent in reagents:
        symbols.add(hx_element(reagent))
        if reagent.GetNumAtoms()!=2: raise ValueError("Mapped HX needs explicit H and X atoms.")
        h=next(a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetAtomicNum()==1)
        x=next(a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetAtomicNum()!=1)
        pairs.append([h,x])
    numbers=[m for p in pairs for m in p]
    if len(symbols)!=1 or len(set(numbers))!=len(numbers) or any(m<=0 for m in numbers):
        raise ValueError("HX equivalents must have the same halogen and unique positive atom maps; mixed donors cannot be substituted.")
    return {"alkyne":[substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]],
            "halogenCarbon":substrate.GetAtomWithIdx(site[2]).GetAtomMapNum(),
            "hydrogenCarbon":substrate.GetAtomWithIdx(next(i for i in site[:2] if i!=site[2])).GetAtomMapNum(),
            "hxPairs":pairs,"halogen":next(iter(symbols)),"equivalents":site[3]}


def edit_contract(substrate, reagents, site):
    p=participants(substrate,reagents,site)
    return [{"atomMaps":p["alkyne"],"before":3.0,"after":float(3-site[3])},
            *[{"atomMaps":pair,"before":1.0,"after":None} for pair in p["hxPairs"]],
            *[{"atomMaps":[p["hydrogenCarbon"],h],"before":None,"after":1.0} for h,_ in p["hxPairs"]],
            *[{"atomMaps":[p["halogenCarbon"],x],"before":None,"after":1.0} for _,x in p["hxPairs"]]]


def validate(before, after, substrate, reagents, site):
    report=assess(substrate,reagents[0],site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    edits=edit_contract(substrate,reagents,site)
    parser=Chem.SmilesParserParams(); parser.removeHs=False
    restored=Chem.MolFromSmiles(Chem.MolToSmiles(after),parser)
    if restored is None: raise ValueError("The mapped HX product cannot survive serialization.")
    for product in (after,restored):
        compatibility.validate_edit_contract(before,product,edits,expected_fragments=1)
        atoms={a.GetAtomMapNum():a for a in product.GetAtoms()}
        bond=product.GetBondBetweenAtoms(*(atoms[m].GetIdx() for m in edits[0]["atomMaps"]))
        if bond.GetStereo()!=Chem.BondStereo.STEREONONE or any(atoms[m].GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED for m in edits[0]["atomMaps"]):
            raise ValueError("Generic alkyne HX addition cannot invent E/Z or local tetrahedral configurations.")
        local=[s for s in stereo.inspect_stereochemistry(product)["alkenes"] if set(s["atomMaps"])==set(edits[0]["atomMaps"])]
        if site[3]==1 and report["internal"]:
            if len(local)!=1 or local[0]["specified"]: raise ValueError("Internal vinyl-halide geometry must remain possible but unassigned, not automatically anti/E/Z.")
        elif local: raise ValueError("Terminal CH2= or fully saturated HX products must not retain or acquire E/Z.")


def metadata(substrate, reagents, site, report):
    p=participants(substrate,reagents,site)
    return {"version":1,**p,"mode":"ionic selected-site net", "selectedBondProductOrder":3-site[3],
            "orientationBasis":report["orientationBasis"],"alternativeOrientations":report["orientationCount"],
            "internal":report["internal"],"oxygenCompetition":report["oxygenCompetition"],"singleSiteBookkeepingOnly":report["singleSiteBookkeepingOnly"],
            "stereoOutcome":"internal vinyl-halide E/Z unassigned" if site[3]==1 and report["internal"] else
                            "terminal CH2 alkene: E/Z not applicable" if site[3]==1 else "saturated geminal dihalide: no local E/Z or new stereocenters",
            "ratios":None,"mechanism":"net only; no validated vinyl-cation or radical intermediate",
            "note":"Actual HX provenance and unchanged physical configurations are checked. Internal orientations are separate constitutional possibilities without preference; generic ionic addition does not establish anti/syn, E/Z or stereoisomer ratios. Coordinates cannot determine reaction selectivity."}
