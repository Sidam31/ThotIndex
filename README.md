# ThotIndex - Registre Indexer

[English](#english) | [Français](#français)

---

<a name="english"></a>
## 🇬🇧 English

### Description
ThotIndex is a tool designed to assist in the indexing of death registers (or similar tabular documents). It allows you to visualize an image of a register page alongside its transcription, verify the data, and correct it efficiently.

### Prerequisites: Generating Data with AI
Before using ThotIndex, you need to generate the initial transcription from your register images.

1.  **Get your image**: Have the image of the register page ready (e.g., `page_01.jpg`).
2.  **Use Google AI Studio**: Go to [aistudio.google.com](https://aistudio.google.com/).
3.  **Select Model**: Choose **Gemini 1.5 Pro** (or newer).
4.  **Upload Image**: Upload your register image to the prompt.
5.  **Use the Prompt**: Copy the content of the `Prompt.txt` file included in this repository and paste it into the chat.
6.  **Generate**: Run the model. It will generate a TSV (Tab-Separated Values) text block.
7.  **Save TSV**: Copy the generated text and save it as a `.tsv` file (e.g., `page_01.tsv`) in the same folder as your image.

### Installation
1.  Ensure you have **Python 3.10+** installed.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Usage
1.  **Start the application**:
    ```bash
    python src/main.py
    ```
2.  **Load Files**:
    *   Go to `File > Load Image...` to open your register image.
    *   Go to `File > Load TSV...` to open the corresponding TSV file.
    *   *Note: The application expects the TSV file to have a specific format with bounding boxes in the first column.*
3.  **Calibration**:
    *   Use the sliders above the table to align the columns of the table with the columns in the image.
    *   You can toggle the visibility of these sliders with the `C` key.
4.  **Navigation**:
    *   **Zoom**: Use `+` / `-` or `Ctrl + Wheel`.
    *   **Pan**: Use `Z/Q/S/D` keys or `Right Click + Drag`.
5.  **Editing**:
    *   Select a row in the table to highlight the corresponding line in the image.
    *   **Edit BBox**: You can resize/move the red bounding box on the image.
    *   **Edit Text**: Double-click a cell in the table to edit the text.
    *   **Add Box**: Press `N` to enter creation mode, then draw a box on the image to add a new row.
6.  **Saving**:
    *   Changes are auto-saved to a `_corr.tsv` file (e.g., `page_01_corr.tsv`).
    *   You can also manually save with `Ctrl + S`.

### Shortcuts
| Action | Shortcut |
|--------|----------|
| Zoom In | `+` |
| Zoom Out | `-` |
| Reset Zoom | `R` |
| Pan Up/Down/Left/Right | `Z`, `S`, `Q`, `D` |
| Toggle Calibration | `C` |
| Add BBox Mode | `N` |
| Save | `Ctrl + S` |
| Undo | `Ctrl + Z` |

---

<a name="français"></a>
## 🇫🇷 Français

### Description
ThotIndex est un outil conçu pour aider à l'indexation des registres de décès (ou documents tabulaires similaires). Il permet de visualiser une image de page de registre à côté de sa transcription, de vérifier les données et de les corriger efficacement.

### Prérequis : Génération des données avec l'IA
Avant d'utiliser ThotIndex, vous devez générer la transcription initiale à partir de vos images de registre.

1.  **Préparez votre image** : Ayez l'image de la page du registre prête (ex: `page_01.jpg`).
2.  **Utilisez Google AI Studio** : Allez sur [aistudio.google.com](https://aistudio.google.com/).
3.  **Sélectionnez le modèle** : Choisissez **Gemini 1.5 Pro** (ou plus récent).
4.  **Importez l'image** : Chargez votre image de registre dans le prompt.
5.  **Utilisez le Prompt** : Copiez le contenu du fichier `Prompt.txt` inclus dans ce dépôt et collez-le dans le chat.
6.  **Générez** : Lancez le modèle. Il générera un bloc de texte au format TSV (valeurs séparées par des tabulations).
7.  **Sauvegardez le TSV** : Copiez le texte généré et sauvegardez-le dans un fichier `.tsv` (ex: `page_01.tsv`) dans le même dossier que votre image.

### Installation
1.  Assurez-vous d'avoir **Python 3.10+** installé.
2.  Installez les dépendances requises :
    ```bash
    pip install -r requirements.txt
    ```

### Utilisation
1.  **Lancer l'application** :
    ```bash
    python src/main.py
    ```
2.  **Charger les fichiers** :
    *   Allez dans `Fichier > Load Image...` pour ouvrir votre image.
    *   Allez dans `Fichier > Load TSV...` pour ouvrir le fichier TSV correspondant.
    *   *Note : L'application attend un format TSV spécifique avec les "bounding boxes" dans la première colonne.*
3.  **Calibration** :
    *   Utilisez les curseurs au-dessus du tableau pour aligner les colonnes du tableau avec celles de l'image.
    *   Vous pouvez afficher/masquer ces curseurs avec la touche `C`.
4.  **Navigation** :
    *   **Zoom** : Utilisez `+` / `-` ou `Ctrl + Molette`.
    *   **Déplacement** : Utilisez les touches `Z/Q/S/D` ou `Clic Droit + Glisser`.
5.  **Édition** :
    *   Sélectionnez une ligne dans le tableau pour mettre en surbrillance la ligne correspondante sur l'image.
    *   **Éditer BBox** : Vous pouvez redimensionner/déplacer la boîte rouge sur l'image.
    *   **Éditer Texte** : Double-cliquez sur une cellule pour modifier le texte.
    *   **Ajouter une boîte** : Appuyez sur `N` pour entrer en mode création, puis dessinez une boîte sur l'image pour ajouter une nouvelle ligne.
6.  **Sauvegarde** :
    *   Les modifications sont sauvegardées automatiquement dans un fichier `_corr.tsv` (ex: `page_01_corr.tsv`).
    *   Vous pouvez aussi sauvegarder manuellement avec `Ctrl + S`.

### Raccourcis
| Action | Raccourci |
|--------|-----------|
| Zoom Avant | `+` |
| Zoom Arrière | `-` |
| Réinitialiser Zoom | `R` |
| Déplacement Haut/Bas/Gauche/Droite | `Z`, `S`, `Q`, `D` |
| Afficher/Masquer Calibration | `C` |
| Mode Ajout BBox | `N` |
| Sauvegarder | `Ctrl + S` |
| Annuler | `Ctrl + Z` |
