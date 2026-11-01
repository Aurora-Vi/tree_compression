# Based on a test script by Mohamed Siala (Stockholm University, 2026), provided for the
# MSc course Research Topics in Data Science. Substantially rewritten by Irina V. Demina ("IVD" below), 2026 
# (shuffled compression, with/without background-knowledge comparison).

from model import Model
from pathlib import Path

HERE = Path(__file__).parent
rules_file = HERE / "rules/rules_derma.txt"
# rules_file = HERE / "rules/rules_cancer.txt"
# background_file = HERE/ "rules/BK_cancer.txt"
SEEDS = range(1000)

def checks(model):
    model.check_satisfiability()
    model.check_all_overlaps()
    model.check_all_redundancies()
    model.check_all_literal_redundancies()

# [Added by IVD] in view of changes by IVD to model.py
print("-" * 50 + "\n" + "-" * 50)
print("Shuffled compression:")

def run(label, background):
    model = Model.from_files(rules_file, background)
    checks(model)
    n_rules = len(model.rules)
    n_lits = sum(len(r.cube) for r in model.rules)
    print("=" * 50)
    print(f"{label}: original {n_rules} rules, {n_lits} literals")
    results = model.compress_with_seeds(SEEDS)
    return results

no_bk = run("WITHOUT background knowledge", None)
# with_bk = run("WITH background knowledge", background_file)

print("=" * 50)
print("SUMMARY")
for label, res in (("no BK", no_bk),):
# for label, res in (("no BK", no_bk), ("with BK", with_bk)):
    sizes = [(len(m.rules), sum(len(r.cube) for r in m.rules)) for m, _ in res.values()]
    print(f"{label}: {len(res)} distinct model(s); (rules, literals) = {sizes}")
