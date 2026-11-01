from pathlib import Path
from model import Model

HERE = Path(__file__).parent
rules = HERE / "rules/rules_derma.txt"
# rules = HERE / "rules/rules_cancer.txt"
# bk = HERE / "rules/BK_cancer.txt"

for seed in (None, 3, 7):
    print("=" * 50)
    print(f"seed = {seed}")
    model = Model.from_files(rules)
    # model = Model.from_files(rules, bk)
    model.compress(seed=seed)
    print("\nAfter removing redundant rules:")
    model.remove_redundant_rules()
    model._print_model()