"""Read-only, reproducible coverage audit; never imported by production code.

Run from the repository root with .venv/bin/python scripts/audit_reaction_lab.py.
--json prints complete observations to stdout. No files or application state are
written. Expected structures below are independently specified net products,
not obtained from the production edit functions. See the accompanying report
for the deliberately bounded meaning of 'Fully supported'.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from server import chemistry_server as service
from server.reaction_information import DEFINITIONS

CASES = []


def case(path, label, substrate, reagent, expected, *, conditions=None,
         partial="", minimum_sites=1, coproducts=None, variant=""):
    CASES.append(dict(path=path, label=label, substrate=substrate, reagent=reagent,
                      expected=expected, conditions=conditions or {}, partial=partial,
                      minimum_sites=minimum_sites, coproducts=coproducts, variant=variant))


def build_matrix():
    # The same substrate classes exercise five independent alkene pathways.
    alkene_rows = [
        ("simple terminal: 1-pentene", "C=CCCC", "CCCCC", "BrCC(Br)CCC", "CC(Br)CCC", "CC(O)CCC", ""),
        ("longer terminal: 1-dodecene", "C=" + "C"*11, "C"*12, "BrCC(Br)"+"C"*10, "CC(Br)"+"C"*10, "CC(O)"+"C"*10, ""),
        ("branched: 2-methyl-1-pentene", "C=C(C)CCC", "CC(C)CCC", "BrCC(Br)(C)CCC", "CC(Br)(C)CCC", "CC(O)(C)CCC", ""),
        ("symmetric internal: 3-hexene", "CCC=CCC", "CCCCCC", "CCC(Br)C(Br)CC", "CCC(Br)CCC", "CCC(O)CCC", ""),
        ("cyclic: cycloheptene", "C1=CCCCCC1", "C1CCCCCC1", "BrC1C(Br)CCCCC1", "BrC1CCCCCC1", "OC1CCCCCC1", "ring"),
        ("position/regio ambiguity: 2-hexene", "CC=CCCC", "CCCCCC", "CC(Br)C(Br)CCC", ["CC(Br)CCCC", "CCC(Br)CCC"], ["CC(O)CCCC", "CCC(O)CCC"], "ambiguous"),
        ("specified E isomer: E-3-hexene", "CC/C=C/CC", "CCCCCC", "CCC(Br)C(Br)CC", "CCC(Br)CCC", "CCC(O)CCC", "stereo"),
        ("specified Z isomer: Z-3-hexene", "CC/C=C\\CC", "CCCCCC", "CCC(Br)C(Br)CC", "CCC(Br)CCC", "CCC(O)CCC", "stereo"),
        ("aromatic conjugation: styrene", "C=Cc1ccccc1", "CCc1ccccc1", "BrCC(Br)c1ccccc1", "CC(Br)c1ccccc1", "CC(O)c1ccccc1", ""),
        ("remote OH: 4-penten-1-ol", "C=CCCCO", "CCCCCO", "BrCC(Br)CCCO", "CC(Br)CCCO", "CC(O)CCCO", ""),
        ("remote F: 5-fluoro-1-pentene", "C=CCCCF", "CCCCCF", "BrCC(Br)CCCF", "CC(Br)CCCF", "CC(O)CCCF", ""),
        ("remote chiral center", "C=CC[C@H](C)CC", "CCC[C@H](C)CC", "BrCC(Br)C[C@H](C)CC", "CC(Br)C[C@H](C)CC", "CC(O)C[C@H](C)CC", ""),
        ("size boundary: 1-triacontene", "C="+"C"*29, "C"*30, "BrCC(Br)"+"C"*28, "CC(Br)"+"C"*28, "CC(O)"+"C"*28, ""),
    ]
    for path, reagent, col, cond in [
        ("Hydrogenation", "hydrogen", 2, {"catalyst":"metal"}),
        ("Bromination", "bromine", 3, {"solvent":"dry"}),
        ("Chlorination", "chlorine", 3, {"solvent":"dry"}),
        ("Hydrohalogenation", "hydrogen-bromide", 4, {}),
        ("Hydration", "water", 5, {"catalyst":"acid"}),
    ]:
        for row in alkene_rows:
            value = row[col]; expected = value if isinstance(value, list) else [value]
            if path == "Chlorination": expected = [s.replace("Br", "Cl") for s in expected]
            partial = "Anti/trans stereochemical outcome is unassigned." if row[-1] == "ring" and path in {"Bromination","Chlorination"} else ""
            case(path, row[0], row[1], reagent, expected, conditions=cond, partial=partial)
        multi = {"Hydrogenation":"C=CCCCCCC", "Bromination":"BrCC(Br)CCCCC=C", "Chlorination":"ClCC(Cl)CCCCC=C", "Hydrohalogenation":"CC(Br)CCCCC=C", "Hydration":"CC(O)CCCCC=C"}
        case(path, "two separated C=C sites: 1,7-octadiene", "C=CCCCCC=C", reagent, [multi[path]], conditions=cond, minimum_sites=2)
        case(path, "negative: saturated pentane", "CCCCC", reagent, None, conditions=cond)
    case("Hydrogenation", "negative: aromatic benzene (ordinary alkene rule)", "c1ccccc1", "hydrogen", None, conditions={"catalyst":"metal"})
    for reagent, x in [("hydrogen-chloride","Cl"),("hydrogen-iodide","I")]:
        case("Hydrohalogenation", "actual reagent: "+reagent, "C=CCCC", reagent, [f"CC({x})CCC"])
    case("Bromination", "negative: iodine substituted for bromine", "C=CCCC", "II", None, conditions={"solvent":"dry"})

    for path, cond in [("Alcohol oxidation",{"solvent":"aqueous-protic","oxidationStage":"first"}),
                       ("Aldehyde oxidation",{"solvent":"aqueous-protic","oxidationStage":"further"})]:
        rows = [("long primary / aldehyde", "CCCCCCCO", "CCCCCCC=O", "CCCCCCC(=O)O"),
                ("branched primary / aldehyde", "CC(C)CCO", "CC(C)CC=O", "CC(C)CC(=O)O"),
                ("aromatic spectator", "OCCc1ccccc1", "O=CCc1ccccc1", "O=C(O)Cc1ccccc1"),
                ("remote ether", "COCCCO", "COCCC=O", "COCCC(=O)O"),
                ("remote F", "OCCCCF", "O=CCCCF", "O=C(O)CCCF"),
                ("remote amine", "NCCCCO", "NCCCC=O", "NCCCC(=O)O"),
                ("remote stereocenter", "CC[C@H](C)CCO", "CC[C@H](C)CC=O", "CC[C@H](C)CC(=O)O"),
                ("unsaturation: allyl alcohol / acrolein", "C=CCO", "C=CC=O", "C=CC(=O)O")]
        for label, alcohol, aldehyde, acid in rows:
            case(path,label,alcohol if path=="Alcohol oxidation" else aldehyde,"sodium-hypochlorite",[aldehyde if path=="Alcohol oxidation" else acid],conditions=cond)
        source = "CCCCCO" if path=="Alcohol oxidation" else "CCCCC=O"
        target = "CCCCC=O" if path=="Alcohol oxidation" else "CCCCC(=O)O"
        case(path,"actual oxidant: potassium hypochlorite",source,"[K+].[O-]Cl",[target],conditions=cond)
        case(path,"negative: ether instead of alcohol/aldehyde","COCCC","sodium-hypochlorite",None,conditions=cond)
    for a,p,label in [("CCCC(O)CCC","CCCC(=O)CCC","secondary: 4-heptanol"),("OC1CCCCCC1","O=C1CCCCCC1","cyclic: cycloheptanol"),("OCCCO","O=CCCO","diol two sites")]:
        case("Alcohol oxidation",label,a,"sodium-hypochlorite",[p],conditions={"solvent":"aqueous-protic"},minimum_sites=2 if "diol" in label else 1)
    case("Alcohol oxidation","negative: tertiary alcohol","CCC(O)(C)C","sodium-hypochlorite",None,conditions={"solvent":"aqueous-protic"})
    case("Aldehyde oxidation","ring spectator: cyclohexanecarbaldehyde","O=CC1CCCCC1","sodium-hypochlorite",["O=C(O)C1CCCCC1"],conditions={"solvent":"aqueous-protic","oxidationStage":"further"})
    case("Aldehyde oxidation","dialdehyde two sites","O=CCCC=O","sodium-hypochlorite",["O=CCCC(=O)O"],conditions={"solvent":"aqueous-protic","oxidationStage":"further"},minimum_sites=2)
    case("Aldehyde oxidation","negative: ketone","CCCC(=O)CCC","sodium-hypochlorite",None,conditions={"solvent":"aqueous-protic","oxidationStage":"further"})

    for label,a,products in [
        ("long aldehyde","CCCCCCC=O",["CCCCCCCO"]),("branched ketone","CC(C)CC(=O)C",["CC(C)CC(O)C"]),
        ("internal ketone","CCCC(=O)CCC",["CCCC(O)CCC"]),("cyclic ketone","O=C1CCCCCC1",["OC1CCCCCC1"]),
        ("aromatic aldehyde","COc1ccc(C=O)cc1",["COc1ccc(CO)cc1"]),
        ("diketone two sites","CC(=O)CCCC(=O)C",["CC(O)CCCC(=O)C"]),
        ("remote F","FCCCCC=O",["FCCCCCO"]),("remote amine","NCCCC=O",["NCCCCO"]),
        ("remote stereocenter","CC[C@H](C)CC=O",["CC[C@H](C)CCO"]),
        ("unsaturated carbonyl","C=CCC=O",["C=CCCO"]),
    ]:
        case("Carbonyl hydrogenation",label,a,"hydrogen",products,conditions={"catalyst":"metal"},minimum_sites=2 if "two sites" in label else 1)
    case("Carbonyl hydrogenation","alternative reductant: sodium borohydride","CCCC(=O)CCC","[Na+].[BH4-]",["CCCC(O)CCC"],conditions={"solvent":"aqueous-protic"})
    case("Carbonyl hydrogenation","negative: carboxylic acid","CCCC(=O)O","hydrogen",None,conditions={"catalyst":"metal"})

    for label,a,b,p,sites in [
        ("long acid and alcohol","CCCCCCC(=O)O","CCCCO","CCCCCCC(=O)OCCCC",1),
        ("branched acid/alcohol","CC(C)C(=O)O","CC(C)CO","CC(C)C(=O)OCC(C)C",1),
        ("cyclic acid and cyclic alcohol","O=C(O)C1CCCCC1","OC1CCCCC1","O=C(OC1CCCCC1)C1CCCCC1",1),
        ("aromatic acid","COc1ccc(C(=O)O)cc1","CCO","COc1ccc(C(=O)OCC)cc1",1),
        ("diacid two acyl sites","O=C(O)CCC(=O)O","CCO","CCOC(=O)CCC(=O)O",2),
        ("diol two alcohol sites","CCCC(=O)O","OCCCO","CCCC(=O)OCCCO",2),
        ("remote ester spectator","COC(=O)CC(=O)O","CO","COC(=O)CC(=O)OC",1),
        ("remote amine on acid","NCCC(=O)O","CO","NCCC(=O)OC",1),
        ("remote stereocenter on acid","CC[C@H](C)CC(=O)O","CO","CC[C@H](C)CC(=O)OC",1),
        ("specified alcohol center","CCCC(=O)O","CC[C@H](O)C","CCCC(=O)O[C@H](C)CC",1),
    ]:
        # Alcohol stereo orientation is checked for connectivity here; blanket
        # rejection is the coverage finding, not a proposed stereoisomer edit.
        case("Esterification",label,a,b,[p],conditions={"catalyst":"acid"},minimum_sites=sites,coproducts=["O"])
    case("Esterification","negative: acid plus ether","CCCC(=O)O","COC",None,conditions={"catalyst":"acid"})

    ester_rows = [
        ("long ester","CCCCCCC(=O)OCCCC","CCCCCCC(=O)O","CCCCO",1),
        ("branched ester","CC(C)C(=O)OCC(C)C","CC(C)C(=O)O","CC(C)CO",1),
        ("cyclic alkoxy group","CCCC(=O)OC1CCCCC1","CCCC(=O)O","OC1CCCCC1",1),
        ("aromatic acyl group","COc1ccc(C(=O)OCC)cc1","COc1ccc(C(=O)O)cc1","CCO",1),
        ("diester two sites","COC(=O)CCCCCC(=O)OC","COC(=O)CCCCCC(=O)O","CO",2),
        ("remote hydroxyl","OCCCC(=O)OCC","OCCCC(=O)O","CCO",1),
        ("aryl alkoxy: phenyl acetate","CC(=O)Oc1ccccc1","CC(=O)O","Oc1ccccc1",1),
        ("lactone ring opening","O=C1OCCC1","OCCCC(=O)O",None,1),
        ("remote amine","NCCCC(=O)OCC","NCCCC(=O)O","CCO",1),
        ("remote stereo","CC[C@H](C)CC(=O)OCC","CC[C@H](C)CC(=O)O","CCO",1),
    ]
    for path,b,cond in [("Ester hydrolysis","water",{"solvent":"aqueous-protic","catalyst":"acid"}),
                        ("Ester saponification","hydroxide",{"solvent":"aqueous-protic"})]:
        for label,a,acid,alcohol,sites in ester_rows:
            product=acid if path=="Ester hydrolysis" else acid.replace("(=O)O","(=O)[O-]")
            case(path,label,a,b,[product],conditions=cond,minimum_sites=sites,coproducts=[] if alcohol is None else [alcohol])
        case(path,"negative: amide","CCCC(=O)N",b,None,conditions=cond)
    case("Ester saponification","actual full salt: KOH","CCCC(=O)OCCC","[K+].[OH-]",["CCCC(=O)[O-]"],conditions={"solvent":"aqueous-protic"},coproducts=["CCCO"])

    for label,a,p in [
        ("long primary","CCCCCCCCCI","CCCCCCCCCO"),("branched primary","CCC(C)CBr","CCC(C)CO"),
        ("secondary","CCCC(Br)CCC","CCCC(O)CCC"),("benzyl","COc1ccc(CBr)cc1","COc1ccc(CO)cc1"),
        ("cyclohexylmethyl (exocyclic)","BrCC1CCCCC1","OCC1CCCCC1"),
        ("ring-bound bromocyclohexane","BrC1CCCCC1","OC1CCCCC1"),
        ("allyl bromide","C=CCBr","C=CCO"),("remote ether","COCCCBr","COCCCO"),
        ("remote F","FCCCCBr","FCCCCO"),
        ("multiple halides two sites","BrCCCCBr","OCCCCBr"),
        ("specified center R input","CC[C@H](Br)CCC","CC[C@@H](O)CCC"),
        ("specified center S input","CC[C@@H](Br)CCC","CC[C@H](O)CCC"),
    ]:
        case("SN2",label,a,"hydroxide",[p],conditions={"solvent":"polar-aprotic"},minimum_sites=2 if "two sites" in label else 1)
    case("SN2","alternative nucleophile: methoxide","CCCCBr","[Na+].[O-]C",["CCCCOC"],conditions={"solvent":"polar-aprotic"})
    case("SN2","alternative nucleophile: iodide","CCCCBr","[Na+].[I-]",["CCCCI"],conditions={"solvent":"polar-aprotic"})
    case("SN2","unsubstituted benzyl bromide","BrCc1ccccc1","hydroxide",["OCc1ccccc1"],conditions={"solvent":"polar-aprotic"})
    for a,label in [("CCC(Br)(C)C","tertiary"),("Brc1ccccc1","aryl"),("C=CBr","vinyl"),("CCCCF","fluoride")]:
        case("SN2","negative: "+label,a,"hydroxide",None,conditions={"solvent":"polar-aprotic"})

    sn1_rows=[("long tertiary","CCCCCC(Br)(C)C","CCCCCC(O)(C)C"),
              ("branched tertiary","CC(C)CC(Br)(C)C","CC(C)CC(O)(C)C"),
              ("benzylic secondary","CC(Br)c1ccccc1","CC(O)c1ccccc1"),
              ("cyclic tertiary","CC1(Br)CCCCC1","CC1(O)CCCCC1"),
              ("allylic tertiary","C=CC(Br)(C)C","C=CC(O)(C)C"),
              ("remote ether","COCCCC(Br)(C)C","COCCCC(O)(C)C"),
              ("remote F","FCCCC(Br)(C)C","FCCCC(O)(C)C"),
              ("specified benzylic center","C[C@H](Br)c1ccccc1","CC(O)c1ccccc1"),
              ("two tertiary sites","CC(Br)(C)CCC(Br)(C)C","CC(O)(C)CCC(Br)(C)C")]
    for label,a,p in sn1_rows:
        case("SN1",label,a,"water",[p],conditions={"solvent":"aqueous-protic","temperature":"ambient"},minimum_sites=2 if "two tertiary" in label else 1)
    case("SN1","alternative trapping solvent: methanol","CCC(Br)(C)C","CO",["CCC(OC)(C)C"],conditions={"temperature":"ambient"})
    case("SN1","secondary aliphatic: possible solvolysis, not a dominant-product claim","CCC(Br)C","water",["CCC(O)C"],conditions={"solvent":"aqueous-protic","temperature":"ambient"})
    case("SN1","negative: methyl carbocation","CBr","water",None,conditions={"solvent":"aqueous-protic"})

    for path,b,solvent in [("E2","hydroxide","ethanolic-protic"),("E1","water","aqueous-protic")]:
        rows=[("tertiary longer chain","CCCC(Br)(C)C",["C=C(C)CCC","CCC=C(C)C"]),
              ("branched tertiary","CC(C)CC(Br)(C)C",["C=C(C)CC(C)C","CC(C)C=C(C)C"]),
              ("ring-bound tertiary","CC1(Br)CCCCC1",["C=C1CCCCC1","CC1=CCCCC1"]),
              ("benzylic secondary","CCC(Br)c1ccccc1",["CC=Cc1ccccc1"]),
              ("remote ether","COCCC(Br)(C)C",["COCC=C(C)C","C=C(C)CCOC"]),
              ("remote F","FCCC(Br)(C)C",["FCCC(C)=C","FCC=C(C)C"]),
              ("remote stereocenter","CC[C@H](C)CCC(Br)(C)C",["CC[C@H](C)CC=C(C)C","C=C(C)CC[C@H](C)CC"])]
        for label,a,p in rows:
            case(path,label,a,b,p,conditions={"solvent":solvent,"temperature":"heated"},partial="E/Z outcome is unassigned." if label=="benzylic secondary" else "")
        case(path,"two tertiary reactive sites","CC(Br)(C)CCC(Br)(C)C",b,["C=C(C)CCC(Br)(C)C","CC(C)=CCC(Br)(C)C"],conditions={"solvent":solvent,"temperature":"heated"},minimum_sites=4)
        case(path,"negative: no beta H (methyl)","CBr",b,None,conditions={"solvent":solvent,"temperature":"heated"})
    for label,a,p in [("long primary","CCCCCCCBr",["C=CCCCCC"]),("secondary internal sites","CCCC(Br)CC",["CCC=CCC","CC=CCCC"]),("cyclic secondary","BrC1CCCCCC1",["C1=CCCCCC1"]),("specified secondary center","CC[C@H](Br)CCC",["CCC=CCC","CC=CCCC"])]:
        case("E2",label,a,"hydroxide",p,conditions={"solvent":"ethanolic-protic","temperature":"heated"},partial="E/Z outcomes are unassigned." if label=="secondary internal sites" else "")
    case("E2","alternative base: potassium tert-butoxide","CCC(Br)(C)C","[K+].[O-]C(C)(C)C",["C=C(C)CC","CC=C(C)C"],conditions={"temperature":"heated"})
    case("E1","secondary aliphatic: possible elimination, not a dominant-product claim","CCC(Br)C","water",["C=CCC","CC=CC"],conditions={"solvent":"aqueous-protic","temperature":"heated"})

    for path,b,cond in [("Alcohol dehydration","sulfuric-acid",{"temperature":"heated","catalyst":"acid"}),
                        ("Alcohol substitution","hydrogen-bromide",{"temperature":"heated"})]:
        rows=[("long primary","CCCCCCCO",["C=CCCCCC"],["CCCCCCCBr"]),
              ("secondary internal","CCCC(O)CC",["CCC=CCC","CC=CCCC"],["CCCC(Br)CC"]),
              ("tertiary branched","CCCC(O)(C)C",["C=C(C)CCC","CCC=C(C)C"],["CCCC(Br)(C)C"]),
              ("cyclic alcohol","OC1CCCCCC1",["C1=CCCCCC1"],["BrC1CCCCCC1"]),
              ("remote ether","COCCCCO",["COCCC=C"],["COCCCCBr"]),
              ("diol multiple groups","OCCCCO",["C=CCCO"],["OCCCCBr"]),
              ("specified center","CC[C@H](O)CCC",["CCC=CCC","CC=CCCC"],["CCCC(Br)CC"]),
              ("benzyl alcohol","OCc1ccccc1",None,["BrCc1ccccc1"])]
        for label,a,dehydrate,substitute in rows:
            if path=="Alcohol dehydration" and dehydrate is None: continue
            case(path,label,a,b,dehydrate if path=="Alcohol dehydration" else substitute,conditions=cond,partial="E/Z outcomes are unassigned." if path=="Alcohol dehydration" and label=="secondary internal" else "")
        case(path,"negative: ether","COCCC",b,None,conditions=cond)
    case("Alcohol dehydration","alternative acid: phosphoric acid","CCCCCO","OP(=O)(O)O",["C=CCCC"],conditions={"catalyst":"acid","temperature":"heated"})
    case("Alcohol dehydration","negative: methanol lacks beta carbon","CO","sulfuric-acid",None,conditions={"catalyst":"acid","temperature":"heated"})
    case("Alcohol substitution","actual HX: HI","CCCCCO","hydrogen-iodide",["CCCCCI"],conditions={"temperature":"heated"})
    case("Alcohol substitution","tertiary HX: HCl","CCCC(O)(C)C","hydrogen-chloride",["CCCC(Cl)(C)C"],conditions={"temperature":"ambient"})
    case("Alcohol substitution","alternative activation: PBr3","CCCCCO","P(Br)(Br)Br",["CCCCCBr"])
    case("Alcohol substitution","negative: bare OH is not activated","CCCCCO","hydroxide",None)

    for path,reagent,cond in [("Epoxidation","peracetic-acid",{"solvent":"dry"}),
                             ("Alkene dihydroxylation","hydrogen-peroxide",{"catalyst":"osmium"})]:
        for label,a,epoxide,diol,partial in [
            ("long terminal","C=CCCCCCC","CCCCCCC1CO1","CCCCCCC(O)CO",""),
            ("branched terminal","C=C(C)CCC","CCCC1(C)CO1","CCCC(O)(C)CO",""),
            ("internal alkene","CCC=CCC","CCC1OC1CC","CCC(O)C(O)CC",""),
            ("cyclic cycloheptene","C1=CCCCCC1","C1CCC2OC2CC1","OC1C(O)CCCCC1","Syn/cis outcome is unassigned."),
            ("remote OH","C=CCCCO","OCCCC1CO1","OCCCC(O)CO",""),
            ("aromatic conjugation","C=Cc1ccccc1","c1ccccc1C1CO1","OCC(O)c1ccccc1",""),
            ("specified E alkene","CC/C=C/CC","CCC1OC1CC","CCC(O)C(O)CC",""),
            ("specified Z alkene","CC/C=C\\CC","CCC1OC1CC","CCC(O)C(O)CC",""),
            ("remote stereocenter","C=CC[C@H](C)CC","CC[C@H](C)CC1CO1","CC[C@H](C)CC(O)CO",""),
        ]:
            case(path,label,a,reagent,[epoxide if path=="Epoxidation" else diol],conditions=cond,partial=partial)
        case(path,"two separated C=C sites","C=CCCCCC=C",reagent,["C=CCCCCC1CO1" if path=="Epoxidation" else "C=CCCCCC(O)CO"],conditions=cond,minimum_sites=2)
        case(path,"negative: saturated alcohol","CCCCO",reagent,None,conditions=cond)
    case("Epoxidation","actual peroxyacid: mCPBA","C=CCCC","O=C(OO)c1cccc(Cl)c1",["CCCC1CO1"],conditions={"solvent":"dry"},coproducts=["O=C(O)c1cccc(Cl)c1"])
    case("Epoxidation","negative: peroxide alone","C=CCCC","hydrogen-peroxide",None)
    case("Alkene dihydroxylation","alternative co-oxidant: NMO","C=CCCC","C[N+]1([O-])CCOCC1",["CCCC(O)CO"],conditions={"catalyst":"osmium"})

    # Alkyne stage variants are separately scored rather than hidden in one row.
    for path in ["Alkyne hydrogenation","Alkyne partial hydrogenation","Alkyne halogenation","Alkyne hydrohalogenation"]:
        stages=[1,2] if path in {"Alkyne halogenation","Alkyne hydrohalogenation"} else [0]
        for n in stages:
            variant=f"{n} equivalent(s)" if n else ""
            reagent={"Alkyne hydrogenation":"hydrogen","Alkyne partial hydrogenation":"hydrogen","Alkyne halogenation":"bromine","Alkyne hydrohalogenation":"hydrogen-bromide"}[path]
            cond={"additionStage":"one" if n==1 else "two"} if n else {"catalyst":"lindlar" if path=="Alkyne partial hydrogenation" else "metal"}
            for label,a,full,part,x1,x2,hx1,hx2,stereo in [
                ("simple: 1-butyne","CCC#C","CCCC","C=CCC","CCC(Br)=CBr","CCC(Br)(Br)C(Br)Br","CCC(Br)=C","CCC(Br)(Br)C",False),
                ("long terminal: 1-decyne","C"*9+"#C","C"*10,"C="+"C"*9,"C"*9+"(Br)=CBr","C"*9+"(Br)(Br)C(Br)Br","C"*9+"(Br)=C","C"*9+"(Br)(Br)C",False),
                ("branched terminal","CC(C)CC#C","CC(C)CCC","CC(C)CC=C","CC(C)CC(Br)=CBr","CC(C)CC(Br)(Br)C(Br)Br","CC(C)CC(Br)=C","CC(C)CC(Br)(Br)C",False),
                ("symmetric internal: 3-hexyne","CCC#CCC","CCCCCC","CCC=CCC","CCC(Br)=C(Br)CC","CCC(Br)(Br)C(Br)(Br)CC","CCC(Br)=CCC","CCC(Br)(Br)CCC",True),
                ("asymmetric internal: 2-hexyne","CC#CCCC","CCCCCC","CC=CCCC","CC(Br)=C(Br)CCC","CC(Br)(Br)C(Br)(Br)CCC",["CC(Br)=CCCC","CCC(Br)=CCC"],["CC(Br)(Br)CCCC","CCC(Br)(Br)CCC"],True),
                ("cyclic: cyclooctyne","C1#CCCCCCC1","C1CCCCCCC1","C1=CCCCCCC1","BrC1=C(Br)CCCCCC1","BrC1(Br)C(Br)(Br)CCCCCC1","BrC1=CCCCCCC1","BrC1(Br)CCCCCCC1",True),
                ("remote OH: 4-pentyn-1-ol","C#CCCCO","CCCCCO","C=CCCCO","BrC=C(Br)CCCO","BrC(Br)C(Br)(Br)CCCO","C=C(Br)CCCO","CC(Br)(Br)CCCO",False),
                ("aromatic conjugation: phenylacetylene","C#Cc1ccccc1","CCc1ccccc1","C=Cc1ccccc1","BrC=C(Br)c1ccccc1","BrC(Br)C(Br)(Br)c1ccccc1","C=C(Br)c1ccccc1","CC(Br)(Br)c1ccccc1",False),
                ("remote stereocenter","C#CC[C@H](C)CC","CCC[C@H](C)CC","C=CC[C@H](C)CC","BrC=C(Br)C[C@H](C)CC","BrC(Br)C(Br)(Br)C[C@H](C)CC","C=C(Br)C[C@H](C)CC","CC(Br)(Br)C[C@H](C)CC",False),
            ]:
                index={"Alkyne hydrogenation":2,"Alkyne partial hydrogenation":3,"Alkyne halogenation":4 if n==1 else 5,"Alkyne hydrohalogenation":6 if n==1 else 7}[path]
                value=(label,a,full,part,x1,x2,hx1,hx2,stereo)[index]
                expected=value if isinstance(value,list) else [value]
                partial=""
                if path=="Alkyne halogenation" and n==1: partial="Dihaloalkene E/Z selectivity is unassigned."
                if path=="Alkyne hydrohalogenation" and n==1 and stereo: partial="Vinyl-halide E/Z outcomes are unassigned."
                case(path,label,a,reagent,expected,conditions=cond,partial=partial,variant=variant)
            multi={"Alkyne hydrogenation":"C#CCCCCCC", "Alkyne partial hydrogenation":"C=CCCCCC#C", "Alkyne halogenation":"BrC=C(Br)CCCCC#C" if n==1 else "BrC(Br)C(Br)(Br)CCCCC#C", "Alkyne hydrohalogenation":"C=C(Br)CCCCC#C" if n==1 else "CC(Br)(Br)CCCCC#C"}
            case(path,"two separated triple bonds: 1,7-octadiyne","C#CCCCCC#C",reagent,[multi[path]],conditions=cond,minimum_sites=2,variant=variant,partial="Dihaloalkene E/Z selectivity is unassigned." if path=="Alkyne halogenation" and n==1 else "")
            case(path,"negative: saturated octane","CCCCCCCC",reagent,None,conditions=cond,variant=variant)
    for path in ["Alkyne halogenation","Alkyne hydrohalogenation"]:
        b="chlorine" if path=="Alkyne halogenation" else "hydrogen-iodide"
        p="CCCC(Cl)=CCl" if path=="Alkyne halogenation" else "CCCC(I)=C"
        case(path,"alternative appropriate halogen", "CCCC#C",b,[p],conditions={"additionStage":"one"},variant="1 equivalent(s)",partial="Dihaloalkene E/Z selectivity is unassigned." if path=="Alkyne halogenation" else "")

    # Independently construct the specified two-chain combination product.
    for units in (2,4,6):
        for label,monomer,sidechain in [("ethylene","C=C",""),("propylene","C=CC","C"),("1-butene","C=CCC","CC"),
                                       ("remote branching: 4-methyl-1-pentene","C=CCC(C)C","CC(C)C"),
                                       ("styrene","C=Cc1ccccc1","c2ccccc2"),
                                       ("vinyl acetate","C=COC(C)=O","OC(C)=O"),
                                       ("acrylonitrile","C=CC#N","C#N")]:
            head="C"+(f"({sidechain})" if sidechain else "")
            product="c1ccccc1"+("C"+head)*(units//2)+(head+"C")*(units//2)+"c1ccccc1"
            case("Polymerization model",label,monomer,"benzoyl-peroxide",[product],conditions={"polymerUnits":str(units),"catalyst":"radical","temperature":"heated"},coproducts=["O=C=O","O=C=O"],variant=f"{units} monomers")
        case("Polymerization model","negative: saturated ethane","CC","benzoyl-peroxide",None,conditions={"polymerUnits":str(units)},variant=f"{units} monomers")


def canonical(s, stereo=True):
    mol=Chem.MolFromSmiles(s)
    if mol is None: raise ValueError("Invalid audit expectation/input: "+s)
    for atom in mol.GetAtoms(): atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(mol, isomericSmiles=stereo)


def reference(s):
    return s if s in service.REACTANTS else {"name":"Independent audit input","smiles":s}


def evaluate(c):
    # Validate independent expectations before invoking production code.
    expected={canonical(s,False) for s in c["expected"] or []}
    a,b=reference(c["substrate"]),reference(c["reagent"])
    r=dict(id=f"A{len(RESULTS)+1:03d}",**c)
    r.update(actual=[],options=0,notes=[],preview="not run",geometry="not run",mechanism_steps=[])
    try:
        match=service.match_reactions(a,b,c["conditions"])
        options=[o for o in match["reactions"] if o["mechanism"]==c["path"]]
        r["notes"]=match["unsupportedReasons"]
    except Exception as e:
        r["status"]="Unsupported" if c["expected"] is not None else "Correctly rejected"
        r["notes"]=[type(e).__name__+": "+str(e)]
        return r
    r["options"]=len(options)
    r["actual"]=sorted({o["productSmiles"] for o in options})
    actual={canonical(s,False) for s in r["actual"]}
    if c["expected"] is None:
        r["status"]="Incorrect result" if options else "Correctly rejected"
        return r
    if not options:
        r["status"]="Unsupported"
        return r
    if actual-expected:
        r["status"]="Incorrect result"; r["notes"].append("Unexpected product connectivity relative to independent expectation.")
    elif expected-actual or len(options)<c["minimum_sites"]:
        r["status"]="Partially supported"; r["notes"].append("Missing expected constitutional product or reaction site.")
    elif c["partial"]:
        # Inspect the actual output, not just the requested feature flag. This
        # audit does not award stereo correctness from connectivity or from
        # a configured tag without an independent expected stereoproduct.
        stereo=[info for option in options for info in Chem.FindPotentialStereo(Chem.MolFromSmiles(option["productSmiles"]))]
        missing=[info for info in stereo if info.specified!=Chem.StereoSpecified.Specified]
        r["observedUnassignedStereoFeatures"]=len(missing)
        r["status"]="Partially supported"
        r["notes"].append(c["partial"] if missing else "Required stereochemical outcome has not been independently verified by this audit; connectivity alone is insufficient.")
    else:
        r["status"]="Fully supported"
    for o in options:
        if not o["stoichiometry"]["balanced"]:
            r["status"]="Incorrect result"; r["notes"].append("Unbalanced serialized equation.")
        try:
            d=service.reaction_diagram(o["id"],a,b,c["conditions"])
            before=[(v["mapId"],v["element"]) for v in d["atoms"] if v["side"]=="reactants"]
            after=[(v["mapId"],v["element"]) for v in d["atoms"] if v["side"]=="products"]
            if len(dict(before))!=len(before) or Counter(before)!=Counter(after) or len(d["atomMap"])!=len(before) or not d["changes"] or not d["highlightsAvailable"]:
                r["status"]="Incorrect result"; r["notes"].append("Map correspondence/conservation/highlights failed.")
            if c["coproducts"] is not None and Counter(canonical(s,False) for s in c["coproducts"])!=Counter(canonical(p["smiles"],False) for p in d["products"][1:]):
                r["status"]="Incorrect result"; r["notes"].append("Independent coproduct expectation failed.")
            m=d["mechanism"]
            r["mechanism_steps"].append(len(m["steps"]) if m else 0)
            if m:
                for step in m["steps"]:
                    before_state=step["beforeState"]; after_state=step["state"]
                    before_ids={v["mapId"]:v["element"] for v in before_state["atoms"]}
                    after_ids={v["mapId"]:v["element"] for v in after_state["atoms"]}
                    before_bonds={tuple(sorted(v["atomMaps"])) for v in before_state["bonds"]}
                    if before_ids!=after_ids or sum(v["formalCharge"] for v in before_state["atoms"])!=sum(v["formalCharge"] for v in after_state["atoms"]):
                        r["status"]="Incorrect result"; r["notes"].append("Independent mechanism atom/charge conservation failed.")
                    for move in step["electronMoves"]:
                        if any(not set(end["atomMaps"])<=set(before_ids) for end in [move["source"],move["destination"]]) or (move["source"]["type"]=="bond" and tuple(sorted(move["source"]["atomMaps"])) not in before_bonds):
                            r["status"]="Incorrect result"; r["notes"].append("Independent electron-source/endpoint validation failed.")
            r["preview"]="verified"
            p=service.run_curated_reaction(o["id"],a,b,c["conditions"])["product"]
            if p["representation"]=="3d":
                diagram_links=[(v["atomIndex"],v["mapId"],v["element"]) for v in d["atoms"] if v["side"]=="products" and v["speciesIndex"]==0]
                model_links=[(v["index"],v["mapId"],v["element"]) for v in p["atomLinks"]]
                if diagram_links!=model_links:
                    r["status"]="Incorrect result"; r["notes"].append("2D/3D exact main-product atom correspondence failed.")
                r["geometry"]="3D; "+("converged" if p["converged"] else "not converged")
            else:
                r["geometry"]="2D-only: "+p["reason"]
        except Exception as e:
            r["notes"].append("Preview/run error: "+type(e).__name__+": "+str(e))
            if r["status"]=="Fully supported": r["status"]="Partially supported"
            r["preview"]="failed"
    # Inversion of these symmetric-order examples has an independent isomeric
    # expectation; a correct graph alone cannot satisfy the two SN2 stereo rows.
    if c["path"]=="SN2" and "specified center" in c["label"] and options:
        if {canonical(s) for s in r["actual"]}!={canonical(s) for s in c["expected"]}:
            r["status"]="Incorrect result"; r["notes"].append("Mapped SN2 physical inversion failed independent stereo expectation.")
    # The same fixed Phase 1 remote-center row now reaches the public matcher.
    # Require its independently specified configuration, not connectivity alone.
    if c["path"]=="Hydrogenation" and "remote chiral center" in c["label"] and options:
        if {canonical(s) for s in r["actual"]}!={canonical(s) for s in c["expected"]}:
            r["status"]="Incorrect result"; r["notes"].append("Remote hydrogenation configuration failed independent stereo expectation.")
    if c["path"]=="Carbonyl hydrogenation" and "remote stereocenter" in c["label"] and options:
        if {canonical(s) for s in r["actual"]}!={canonical(s) for s in c["expected"]}:
            r["status"]="Incorrect result"; r["notes"].append("Remote carbonyl-reduction configuration failed independent stereo expectation.")
    if c["path"]=="Alcohol oxidation" and "remote stereocenter" in c["label"] and options:
        if {canonical(s) for s in r["actual"]}!={canonical(s) for s in c["expected"]}:
            r["status"]="Incorrect result"; r["notes"].append("Remote alcohol-oxidation configuration failed independent stereo expectation.")
    return r


RESULTS=[]


def supplementary_probes():
    """Separate observations; not mixed into the structural percentage scores."""
    from server import reaction_engine as engine, molecular_graph as graph
    from server.reaction_diagrams import _species, _identity
    direct=[]
    for mechanism in ("Ester hydrolysis","Ester saponification"):
        for substrate in ("O=C1OCCC1","CC(=O)Oc1ccccc1"):
            mol=Chem.MolFromSmiles(substrate); carbon,oxo=graph.find_carbonyls(mol)[0]
            oxygen=next(a for a in mol.GetAtomWithIdx(carbon).GetNeighbors() if a.GetSymbol()=="O" and a.GetIdx()!=oxo)
            other=next(a for a in oxygen.GetNeighbors() if a.GetSymbol()=="C" and a.GetIdx()!=carbon)
            a,n=_species("a",{"name":"Audit substrate","smiles":substrate},1)
            b,n=_species("b",{"name":"Audit reagent","smiles":"O" if mechanism=="Ester hydrolysis" else "[OH-]"},n)
            outputs=engine.transform(mechanism,[a,b],(carbon,oxo,oxygen.GetIdx(),other.GetIdx()))
            direct.append({"path":mechanism,"substrate":substrate,"products":[_identity(f) for f in outputs],"note":"Supplementary direct-transform observation only; public-workflow support is scored separately in the unchanged matrix."})
    conditions=[]
    for a,b,c in [("ethene","hydrogen",{"catalyst":"none"}),("ethene","water",{"catalyst":"none","solvent":"dry"}),
                  ("ethene","hydrogen-peroxide",{"catalyst":"none"}),("CCCCCO","sulfuric-acid",{"temperature":"ambient","catalyst":"none"}),
                  ("CCCCC=O","sodium-hypochlorite",{}),("CCCCC=O","sodium-hypochlorite",{"oxidationStage":"further","solvent":"aqueous-protic"})]:
        matches=service.match_reactions(reference(a),reference(b),c)
        conditions.append({"substrate":a,"reagent":b,"conditions":c,"results":[{"path":r["mechanism"],"assessment":r["assessment"],"label":r["reasoning"]["label"]} for r in matches["reactions"]]})
    return {"direct_transforms":direct,"conditions":conditions}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--json",action="store_true"); args=parser.parse_args()
    RDLogger.DisableLog("rdApp.warning"); RDLogger.DisableLog("rdApp.error")
    build_matrix()
    for c in CASES: RESULTS.append(evaluate(c))
    summaries={}
    for path in DEFINITIONS:
        rows=[r for r in RESULTS if r["path"]==path]; valid=[r for r in rows if r["expected"] is not None]
        full=sum(r["status"]=="Fully supported" for r in valid)
        summaries[path]={"fully_supported":full,"applicable":len(valid),"score":round(100*full/len(valid),1),"statuses":dict(Counter(r["status"] for r in rows))}
    variants={}
    for r in RESULTS:
        if r["variant"]:
            key=r["path"]+" / "+r["variant"]; variants.setdefault(key,[]).append(r)
    variants={key:{"fully_supported":sum(r["status"]=="Fully supported" for r in rows if r["expected"] is not None),"applicable":sum(r["expected"] is not None for r in rows)} for key,rows in variants.items()}
    files=["server/reaction_engine.py","server/extended_reaction_rules.py","server/reaction_mechanisms.py","server/stereochemistry.py","server/reaction_diagrams.py","server/chemistry_server.py","src/reaction-lab.ts",
           "server/molecular_graph.py","server/ester_rules.py","server/reaction_compatibility.py","server/hydrogenation_rule.py","server/carbonyl_hydrogenation_rule.py","server/alcohol_oxidation_rule.py","server/sn2_rule.py","server/e2_rule.py","server/sn1_rule.py","server/e1_rule.py"]
    payload={"case_count":len(RESULTS),"applicable":sum(r["expected"] is not None for r in RESULTS),"statuses":dict(Counter(r["status"] for r in RESULTS)),"summaries":summaries,"variants":variants,"production_sha256":{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files},"rdkit_version":Chem.rdBase.rdkitVersion,"supplementary":supplementary_probes(),"results":RESULTS}
    if args.json: print(json.dumps(payload,separators=(",",":")))
    else:
        print(json.dumps({k:v for k,v in payload.items() if k!="results"},indent=2))
        for r in RESULTS:
            if r["status"]=="Incorrect result" or r["preview"]=="failed": print(r["id"],r["path"],r["label"],r["actual"],r["notes"])


if __name__=="__main__": main()
