"""Independent Phase 4D graph, stoichiometry, parity and public service checks."""
import hashlib
import json
import unittest
from pathlib import Path
from rdkit import Chem
from server import chemistry_server as service, reaction_engine as engine, alkyne_hydrohalogenation_rule as rule
from server import molecular_graph as graph, stereochemistry as stereo
from server.reaction_diagrams import _species, _combine, mapped_product_molecule

FIXTURE=json.loads(Path("tests/fixtures/alkyne-hydrohalogenation.json").read_text())
REAGENTS={"Cl":"hydrogen-chloride","Br":"hydrogen-bromide","I":"hydrogen-iodide"}
CONDITIONS={"solvent":"dry","temperature":"ambient"}


def canonical(smiles): return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def options(source, symbol="Br", stage="one", conditions=None, reverse=False):
    a,b={"name":"Independent HX substrate","smiles":source},REAGENTS.get(symbol,symbol) if isinstance(symbol,str) else symbol
    if reverse: a,b=b,a
    c={**CONDITIONS,"additionStage":stage} if conditions is None else conditions
    m=service.match_reactions(a,b,c)
    return a,b,c,m,[r for r in m["reactionOptions"] if r["mechanism"]==rule.PATHWAY]


def permission(case,symbol,stage):
    return (not case.get("oxygen") and not case.get("bookkeepingOnly") and symbol!="Cl"
            and not (stage=="one" and case.get("internal")) and not (symbol=="I" and stage=="two"))


def physical_parity(atom):
    ns=[n.GetAtomMapNum() for n in atom.GetNeighbors()]
    inversions=sum(ns[i]>ns[j] for i in range(len(ns)) for j in range(i+1,len(ns)))
    return bool(inversions%2) ^ (atom.GetChiralTag()==Chem.ChiralType.CHI_TETRAHEDRAL_CW)


def inputs(source="CC#CCC", symbol="Br", count=1, target=None):
    a,n=_species("a",{"name":"source","smiles":source},1); result=[a]
    for _ in range(count):
        b,n=_species("b",{"name":"HX","smiles":symbol},n); result.append(b)
    ends=graph.find_alkynes(a["mol"])[0]
    if target is None: target=rule.orientations(a["mol"],ends)[0][0]
    return result,(*ends,target,count)


class AlkyneHxTests(unittest.TestCase):
    def positive(self,case,symbol,stage):
        for reverse in (False,True):
            a,b,c,m,found=options(case["substrate"],symbol,stage,reverse=reverse)
            expected={canonical(p.replace("Br",symbol)) for p in case[stage]}
            self.assertEqual({r["productSmiles"] for r in found},expected)
            legacy=[r for r in m["reactions"] if r["mechanism"]==rule.PATHWAY]
            self.assertEqual(len(legacy),case.get("legacySites",len(found)))
            for r in found:
                n=1 if stage=="one" else 2; model=r["alkyneHxModel"]
                allowed=permission(case,symbol,stage)
                self.assertEqual(r["assessment"]["canRun"],bool(allowed))
                self.assertEqual(model["halogen"],symbol); self.assertEqual(model["equivalents"],n)
                self.assertEqual(model["selectedBondProductOrder"],3-n)
                self.assertIsNone(r["regioselectivity"]["ratios"])
                self.assertNotIn(r["reasoning"]["label"],{"Strong match","Unfavorable"})
                basis=r["stoichiometry"]
                hx=next(v for v in basis["reactants"] if v["formula"]=="H"+symbol)
                self.assertEqual(hx["coefficient"],n); self.assertEqual(hx["inputSlot"],0 if reverse else 1)
                self.assertAlmostEqual(sum(v["coefficient"]*v["molarMass"] for v in basis["reactants"]),basis["product"]["molarMass"],places=6)
                self.assertEqual(basis["context"]["canGenerate3D"],bool(allowed))
                self.assertIn("not actual supply or stopping",basis["context"]["warning"])
                self.assertIn("radical initiation absence",r["assessment"]["evidence"]["unknownConditions"])
                self.assertEqual(r["byproducts"],[])
                d=service.reaction_diagram(r["id"],a,b,c)
                self.assertIsNone(d["mechanism"])
                self.assertEqual(r["information"]["capabilities"]["mappedMechanism"],"unsupported")
                self.assertEqual(len(d["bondsBroken"]),n); self.assertEqual(len(d["bondsFormed"]),2*n)
                self.assertEqual([(e["before"],e["after"]) for e in d["bondOrderChanges"]],[(3,3-n)])
                before=[v for v in d["atoms"] if v["side"]=="reactants"]
                after=[v for v in d["atoms"] if v["side"]=="products"]
                identity=lambda xs:{v["mapId"]:(v["element"],v["formalCharge"]) for v in xs}
                self.assertEqual(identity(before),identity(after)); self.assertEqual(len(before),len(after))
                self.assertEqual(len(identity(before)),len(before))
                self.assertEqual({frozenset(e["atomMaps"]) for e in d["bondsBroken"]},{frozenset(p) for p in model["hxPairs"]})
                expected_formations={frozenset((model["hydrogenCarbon"],h)) for h,_ in model["hxPairs"]}|{frozenset((model["halogenCarbon"],x)) for _,x in model["hxPairs"]}
                self.assertEqual({frozenset(e["atomMaps"]) for e in d["bondsFormed"]},expected_formations)
                for h,x in model["hxPairs"]:
                    self.assertEqual(identity(before)[h],("H",0)); self.assertEqual(identity(before)[x],(symbol,0))
                ids,custom,_=service._resolve_reactants(a,b); catalog={**service.REACTANTS,**custom}
                reaction=service._reactions_for_pair(*ids,catalog,service._conditions(c))[0][r["id"]]
                product=mapped_product_molecule(reaction,catalog)
                original,_=_species("original",catalog[reaction["reactants"][0]],1)
                indexed={v.GetAtomMapNum():v for v in product.GetAtoms()}
                for atom in original["mol"].GetAtoms():
                    if atom.GetChiralTag() in stereo.TETRAHEDRAL:
                        self.assertEqual(physical_parity(atom),physical_parity(indexed[atom.GetAtomMapNum()]))
                local=[v for v in r["stereochemistry"]["product"]["alkenes"] if set(v["atomMaps"])==set(r["site"]["atomMaps"])]
                if case.get("internal") and stage=="one":
                    self.assertEqual(len(local),1); self.assertIsNone(local[0]["assignment"]); self.assertFalse(local[0]["specified"])
                else:self.assertEqual(local,[])
                self.assertFalse(any(v["specified"] and v["atomMap"] in r["site"]["atomMaps"] for v in r["stereochemistry"]["product"]["chiralCenters"]))
                self.assertEqual(len(graph.find_alkynes(product)),len(graph.find_alkynes(original["mol"]))-1)
                self.assertIn("Conditional",d["note"])
                if not allowed:
                    with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r["id"],a,b,c)
                    continue
                p=service.run_curated_reaction(r["id"],a,b,c)["product"]
                self.assertEqual(p["representation"],"3d"); self.assertEqual(p["smiles"],r["productSmiles"])
                self.assertEqual([(v["atomIndex"],v["mapId"],v["element"]) for v in after],[(v["index"],v["mapId"],v["element"]) for v in p["atomLinks"]])
                shape=Chem.MolFromMolBlock(p["molfile"],removeHs=False)
                self.assertTrue(shape.GetConformer().Is3D())
                for atom in shape.GetAtoms(): atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
                Chem.AssignStereochemistryFrom3D(shape,replaceExistingTags=True)
                assignments={v["atomMap"]:v["assignment"] for v in stereo.inspect_stereochemistry(shape)["chiralCenters"]}
                for v in r["stereochemistry"]["product"]["chiralCenters"]:
                    if v["specified"]:self.assertEqual(assignments[v["atomMap"]],v["assignment"])

    def negative(self,case):
        for symbol in REAGENTS:
            for stage in ("one","two"):
                _,_,_,m,found=options(case["substrate"],symbol,stage)
                self.assertFalse(found)
                if case.get("reason"): self.assertIn(case["reason"].lower()," ".join(m["unsupportedReasons"]).lower())

    def test_terminal_markovnikov_vs_internal_alternatives_golden_products(self):
        self.assertEqual(options("CCC#C")[-1][0]["productSmiles"],"C=C(Br)CC")
        self.assertEqual({r["productSmiles"] for r in options("CC#CCC")[-1]}, {canonical("CC(Br)=CCC"),canonical("CC=C(Br)CC")})
        self.assertEqual({r["productSmiles"] for r in options("CC#CCCC",stage="two")[-1]}, {canonical("CC(Br)(Br)CCCC"),canonical("CCC(Br)(Br)CCC")})
        self.assertEqual(len(options("CCC#CCC")[-1]),1)
        alternatives=options("CC#CCC")[-1]
        self.assertEqual(len({r["site"]["label"] for r in alternatives}),2)
        self.assertTrue(all("halogen → carbon "+str(r["regioselectivity"]["halogenCarbonMap"]) in r["site"]["label"] for r in alternatives))

    def test_internal_geometry_is_not_automatically_anti_trans_e_or_z(self):
        for symbol in REAGENTS:
            for r in options("CC#CCC",symbol)[-1]:
                self.assertNotIn("/",r["productSmiles"]); self.assertNotIn("\\",r["productSmiles"])
                self.assertIn("E/Z unassigned",r["alkyneHxModel"]["stereoOutcome"])
                self.assertFalse(r["assessment"]["canRun"])

    def test_hcl_hbr_hi_policies_are_independent_not_synonyms(self):
        for symbol,expected in (("Cl",[False,False]),("Br",[True,True]),("I",[True,False])):
            actual=[options("CCC#C",symbol,stage)[-1][0]["assessment"]["canRun"] for stage in ("one","two")]
            self.assertEqual(actual,expected)
        for catalyst in ("metal","acid","lindlar","osmium"):
            r=options("CCC#C","Cl",conditions={**CONDITIONS,"additionStage":"one","catalyst":catalyst})[-1][0]
            self.assertFalse(r["assessment"]["canRun"])

    def test_condition_omissions_capture_and_radicals_remain_conditional(self):
        for c in ({},{"additionStage":"one"},{"solvent":"dry","additionStage":"one"},{"solvent":"dry","temperature":"ambient"},
                  {**CONDITIONS,"additionStage":"one","catalyst":"radical"},
                  {**CONDITIONS,"additionStage":"two","temperature":"heated"},
                  {**CONDITIONS,"additionStage":"one","solvent":"aqueous-protic"},
                  {**CONDITIONS,"additionStage":"one","solvent":"ethanolic-protic"},
                  {**CONDITIONS,"additionStage":"one","solvent":"polar-aprotic"}):
            a,b,_,_,found=options("CCC#C",conditions=c); self.assertEqual(len(found),1)
            r=found[0]; self.assertFalse(r["assessment"]["canRun"])
            self.assertNotIn(r["assessment"]["status"],{"disfavored","reference-difference"})
            self.assertTrue(service.reaction_diagram(r["id"],a,b,c)["svg"])
            with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r["id"],a,b,c)

    def test_oxygen_bonds_are_not_called_experimentally_inert(self):
        for symbol in REAGENTS:
            r=options("C#CCCCCCOC",symbol)[-1][0]
            self.assertTrue(r["alkyneHxModel"]["oxygenCompetition"])
            self.assertFalse(r["assessment"]["canRun"])
            self.assertIn("cleavage",r["assessment"]["note"])
            self.assertIn("conditional bookkeeping",r["stoichiometry"]["context"]["warning"])

    def test_equivalent_site_aliases_are_still_independently_addressable(self):
        a,b,c,m,found=options("C#CCCCCC#C")
        self.assertEqual(len(found),1); self.assertEqual(found[0]["optionIdentity"]["siteCount"],2)
        for identifier in found[0]["optionIdentity"]["sourceReactionIds"]:
            self.assertEqual(service.reaction_diagram(identifier,a,b,c)["site"]["siteId"],identifier)
        self.assertEqual(len(options("C#CCCCCC(C)CC#C")[-1]),2)

    def test_symmetry_and_orientation_are_not_based_on_atom_numbering(self):
        original=Chem.MolFromSmiles("CC#CCCC")
        reordered=Chem.MolToSmiles(Chem.RenumberAtoms(original,list(reversed(range(original.GetNumAtoms())))),canonical=False)
        self.assertEqual({r["productSmiles"] for r in options("CC#CCCC")[-1]},{r["productSmiles"] for r in options(reordered)[-1]})

    def test_stale_stage_halogen_and_condition_permissions_do_not_survive(self):
        a,b,c,_,found=options("CCC#C"); identifier=found[0]["id"]
        with self.assertRaises(service.ChemistryError):service.reaction_diagram(identifier,a,b,{**c,"additionStage":"two"})
        with self.assertRaises(service.ChemistryError):service.run_curated_reaction(identifier,a,"hydrogen-chloride",c)
        with self.assertRaises(service.ChemistryError):service.run_curated_reaction(identifier,a,b,{"additionStage":"one"})

    def test_wrong_reagents_and_unrecognized_conditions(self):
        for reagent in ("hydrogen","water","bromine","chlorine",{"smiles":"F"},{"smiles":"[Cl-]"},{"smiles":"BrCl"}):
            try:self.assertFalse(options("CCC#C",reagent)[-1])
            except service.ChemistryError:pass
        for c in ({"additionStage":"3"},{"additionStage":"excess"},{"catalyst":"peroxide"},{"solvent":"DMPU"}):
            with self.assertRaises(service.ChemistryError):options("CCC#C",conditions=c)

    def test_raw_stereo_is_never_silently_discarded(self):
        for src in ("C#CC[C@H](C)CC |&1:3|","C#C[C@H](C)C","C/C#CC"):
            try:
                _,_,_,m,found=options(src); self.assertFalse(found); self.assertTrue(m["unsupportedReasons"])
            except service.ChemistryError:pass

    def test_two_actual_donors_and_exact_incoming_atom_identities(self):
        ins,site=inputs(count=2)
        for reagents in ([ins[1]["mol"]],[ins[1]["mol"]]*2):
            with self.assertRaises(ValueError):rule.participants(ins[0]["mol"],reagents,site)
        chlorine,_=_species("cl",{"name":"chloride","smiles":"Cl"},100)
        with self.assertRaises(ValueError):rule.participants(ins[0]["mol"],[ins[1]["mol"],chlorine["mol"]],site)
        for wrong in ("F","BrBr","[Br-]","[2H]Br","[H][81Br]"):
            with self.assertRaises(ValueError):rule.hx_element(Chem.MolFromSmiles(wrong))

    def test_exact_edit_validator_rejects_rearrangement_and_invented_ez(self):
        ins,site=inputs(); before=_combine(ins); product=engine.transform(rule.PATHWAY,ins,site)[0]
        rule.validate(before,product,ins[0]["mol"],[ins[1]["mol"]],site)
        for state in (Chem.BondStereo.STEREOE,Chem.BondStereo.STEREOZ):
            bad=Chem.Mol(product); bond=bad.GetBondBetweenAtoms(*site[:2])
            a,b=bond.GetBeginAtom(),bond.GetEndAtom()
            refs=[next(n.GetIdx() for n in v.GetNeighbors() if n.GetIdx()!=other.GetIdx()) for v,other in ((a,b),(b,a))]
            bond.SetStereoAtoms(*refs); bond.SetStereo(state)
            with self.assertRaises(ValueError):rule.validate(before,bad,ins[0]["mol"],[ins[1]["mol"]],site)
        bad=Chem.RWMol(product)
        bond=next(b for b in bad.GetBonds() if b.GetBeginAtom().GetAtomicNum()==b.GetEndAtom().GetAtomicNum()==6 and b.GetBondType()==Chem.BondType.SINGLE)
        bond.SetBondType(Chem.BondType.DOUBLE)
        with self.assertRaises(ValueError):rule.validate(before,bad,ins[0]["mol"],[ins[1]["mol"]],site)

    def test_terminal_wrong_orientation_is_rejected_not_overridden(self):
        ins,site=inputs(source="CCC#C")
        wrong=(*site[:2],next(i for i in site[:2] if i!=site[2]),1)
        self.assertFalse(rule.assess(ins[0]["mol"],ins[1]["mol"],wrong)["eligible"])
        with self.assertRaises(ValueError):engine.transform(rule.PATHWAY,ins,wrong)

    def test_remote_ordinary_carbocycle_is_preserved_not_opened(self):
        source="C#CCCC1CCCCC1"
        a,b,c,_,found=options(source)
        self.assertEqual(len(found),1)
        product=Chem.MolFromSmiles(found[0]["productSmiles"])
        self.assertEqual([len(r) for r in product.GetRingInfo().AtomRings()],[6])
        self.assertEqual(service.run_curated_reaction(found[0]["id"],a,b,c)["product"]["representation"],"3d")

    def test_size_limit_includes_added_hydrogen_and_halogen(self):
        _,_,_,m,found=options("C"*26+"#C")
        self.assertFalse(found); self.assertIn("80 explicit atoms"," ".join(m["unsupportedReasons"]))

    def test_fixed_wrong_internal_expectation_is_not_copied_into_products(self):
        actual={r["productSmiles"] for r in options("CC#CCCC")[-1]}
        self.assertNotIn(canonical("CCC(Br)=CCC"),actual)
        self.assertIn(canonical("CC=C(Br)CCC"),actual)
        self.assertEqual(hashlib.sha256(Path("scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
                         "1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55")

    def test_cip_label_changes_without_physical_inversion(self):
        a,b,c,_,found=options("C#CCC[C@H](C)CCCO",stage="two")
        self.assertEqual(len(found),1);r=found[0]
        self.assertEqual(r["stereochemistry"]["reactant"]["chiralCenters"][0]["assignment"],"S")
        self.assertEqual(r["stereochemistry"]["product"]["chiralCenters"][0]["assignment"],"R")
        ids,custom,_=service._resolve_reactants(a,b);catalog={**service.REACTANTS,**custom}
        reaction=service._reactions_for_pair(*ids,catalog,service._conditions(c))[0][r["id"]]
        original,_=_species("original",catalog[reaction["reactants"][0]],1)
        product=mapped_product_molecule(reaction,catalog)
        old=next(a for a in original["mol"].GetAtoms() if a.GetChiralTag() in stereo.TETRAHEDRAL)
        new=next(a for a in product.GetAtoms() if a.GetAtomMapNum()==old.GetAtomMapNum())
        self.assertEqual(physical_parity(old),physical_parity(new))
        # Oxygen competition still prevents an experimental-looking 3D claim.
        self.assertFalse(r["assessment"]["canRun"])


for i,case in enumerate(FIXTURE["positive"]):
    for symbol in REAGENTS:
        for stage in ("one","two"):
            def positive_test(self,case=case,symbol=symbol,stage=stage):self.positive(case,symbol,stage)
            setattr(AlkyneHxTests,f"test_positive_{i:02d}_{symbol}_{stage}",positive_test)
for i,case in enumerate(FIXTURE["negative"]):
    def negative_test(self,case=case):self.negative(case)
    setattr(AlkyneHxTests,f"test_negative_{i:02d}",negative_test)
