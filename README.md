# Compression of a Decision Tree for Classification of Erythemato-squamous Diseases

This project applies a decision tree (max depth 6, min samples per leaf 3) to the UCI Dermatology dataset and extracts 8 decision rules (R1–R8) to classify 6 erythemato-squamous diseases.

**Author:** Irina V. Demina 

## Repository Contents
- `notebook.ipynb` – Main Jupyter notebook with analysis and results.
- `requirements.txt` – Python packages needed to run the notebook.
- `rules.txt` (or `rules.md`) – The rule list used in the project.
- `dataset/` – Folder containing the dermatology dataset.

## How to Run
1. Install the required packages:
   ```bash```
   pip install -r requirements.txt
2. Open the notebook:
   ```bash```
   jupyter notebook notebook.ipynb
3. Run all cells from top to bottom.

## Dataset
Ilter, N. & Guvenir, H. (1998). Dermatology [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5FK5P.

Size: 366 instances, 34 features, i.e. 32 are ordinal/integer-coded (0–3), 1 numerical/integer (age) and 1 binary feature (family history).


Target: 6 dermatology classes:
- psoriasis
- seborrheic dermatitis
- lichen planus
- pityriasis rosea
- chronic dermatitis
- pityriasis rubra pilaris

Notes: 8 missing values in the column `Age`.

## Rule List
The final decision tree was trained using scikit-learn's `DecisionTreeClassifier` with `max_depth=6` and `min_samples_leaf=3`. The trained tree was then converted into 8 decision rules (R1–R8) to classify the 6 diseases.

## Acknowledgments
Dataset provided by the UCI Machine Learning Repository.


