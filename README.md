# Compression of two decision sets, each derived from a decision tree learned from a corresponding medical dataset


**Author:** Irina V. Demina

## Repository Contents
- `trees/` – Decision tree training and rule extraction.
  - `derma_tree.ipynb` – Dermatology decision tree and rules.
  - `breast_cancer_tree.ipynb` – Breast cancer decision tree.
  - `dermatology/` – UCI Dermatology data (`dermatology.data`, `dermatology.names`).
  - `compressed_derma.txt`, `compressed_cancer_BK.txt` – Compressed rule sets.
- `rule_compression/` – SAT-based rule compression (uses `python-sat`).
  - `model.py` – `Model` class: satisfiability, overlap and redundancy checks, compression.
  - `test_model.py` – Compresses rules over many random shuffles with and without background knowledge.
  - `check_shuffling.py` – Compares compressed models across shuffle seeds.
  - `rules/` – Input rules (`rules_derma.txt`, `rules_cancer.txt`) and background knowledge (`BK_cancer.txt`).
  - `result_*.txt` – Output of the experiments.
- `requirements.txt` – Python packages needed to run everything.

## How to Run
1. Install the required packages (Python 3.13 tested):
   ```bash
   pip install -r requirements.txt
   ```
2. Decision trees: open a notebook in `trees/` and run all cells from top to bottom:
   ```bash
   jupyter notebook trees/derma_tree.ipynb
   ```
3. Rule compression: run from the repository root:
   ```bash
   python rule_compression/test_model.py
   python rule_compression/check_shuffling.py
   ```
   Switch between the dermatology and breast cancer rules by editing the file paths at the top of each script.

## Datasets

### Dermatology
Ilter, N. & Guvenir, H. (1998). Dermatology [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5FK5P.

Size: 366 instances, 34 features: 32 ordinal/integer-coded (0–3), 1 numerical/integer (age) and 1 binary (family history).

Target: 6 dermatology classes:
- psoriasis
- seborrheic dermatitis
- lichen planus
- pityriasis rosea
- chronic dermatitis
- pityriasis rubra pilaris

Notes: 8 missing values in the column `Age`.

### Breast Cancer Wisconsin (Diagnostic)
Wolberg, W., Mangasarian, O., Street, N. & Street, W. (1993). Breast Cancer Wisconsin (Diagnostic) [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B.

Loaded in `trees/breast_cancer_tree.ipynb` with scikit-learn's `load_breast_cancer`, so no separate download is needed.

Size: 569 instances, 30 numeric features.

Target: 2 classes, malignant (`0`) and benign (`1`) in the scikit-learn encoding.

Notes: no missing values.

## Decision Trees and Rules
- **Dermatology:** scikit-learn's `DecisionTreeClassifier` with `max_depth=6` and `min_samples_leaf=3`, converted into 8 decision rules (R1–R8) that classify the 6 diseases.
- **Breast cancer:** `DecisionTreeClassifier` with `max_depth=4` and `min_samples_leaf=2`, converted into 12 decision rules (R1-R12) that classify the two types of tumours.

## Rule Compression
`rule_compression/model.py` encodes the rules as propositional clauses and uses a SAT solver to check satisfiability, overlaps and redundancies and to compress the rule set. Compression is repeated over random shuffles of the rule and literal order to compare the resulting models; for the breast cancer rules it is also run with background knowledge.

## Acknowledgments
`rule_compression/model.py` is based on the code by Mohamed Siala (Stockholm University, 2026), provided in the frame of the MSc course Research Topics in Data Science, and modified by the author.

Datasets provided by the UCI Machine Learning Repository.

