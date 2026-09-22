# Email Automation — Envoi par dossiers

Application Python pour l'envoi automatisé d'e-mails personnalisés à partir d'une arborescence de dossiers.


## Installation
Cloner le repertoire
```bash
git clone Email-Automatisation
cd Email-Automatisation

Creation d'un environement virtuelle
python -m venv venv
venv\Scripts\activate           # Windows

Installation des requiremts
pip install -r requirements.txt

Modification des variables d'environnement
cp .env
```

---

## Structure des dossiers

```
emails/
├── client_A/
│   ├── config.json       ← Obligatoire a configurer pour chaque dossier
│   ├── test.txt
└── client_B/
    ├── config.json
    └── rapport.xlsx
```

### Format `config.json`
Voici le format de configuration des fichier Json pour chaque dossier
```json
{
  "destinataire": "client@example.com",
  "cc": ["copie@example.com"],
  "cci": ["archive@example.com"],
  "sujet": "Votre facture du mois",
  "variables": {
    "nom": "M. Dupont",
    "montant": "150 000 FCFA",
    "date": "15/01/2025"
  }
}
```

---

## Utilisation

### Mode test (aucun mail envoyé)
```bash
python main.py --dry-run
```

### Envoi réel
```bash
python main.py
```

### Options disponibles
```
--dir <chemin>        Répertoire racine des dossiers (override .env)
--template <chemin>   Chemin vers le template (override .env)
--dry-run             Mode test, aucun envoi
--retry-failed        Relancer uniquement les dossiers en échec
```

---

## Logs
Il existe un fichier dans lequel on peut retrouver tous les logs et les details de chaque envoie de mail
- `logs/envois.log` — journal détaillé
- `logs/envois.csv` — tableau CSV (horodatage, dossier, destinataire, statut, erreur)

---

## Sécurité

- Ne jamais mettre de mot de passe dans le code
- Gmail/Outlook : utiliser un **mot de passe d'application** (pas le mot de passe principal)

### Gmail — mot de passe d'application
1. Activez la validation en 2 étapes
2. Allez dans Mon compte → Sécurité → Mots de passe des applications
3. Générez un mot de passe pour "Courrier"
4. Copiez-le dans `SMTP_PASSWORD` dans `.env`

---

## Configuration SMTP courante

| Fournisseur | SMTP_HOST           | SMTP_PORT |
|-------------|---------------------|-----------|
| Gmail       | smtp.gmail.com      | 587       |
| Outlook     | smtp.office365.com  | 587       |
| Yahoo       | smtp.mail.yahoo.com | 587       |
| Perso       | mail.votredomaine.com | 587 ou 465 |
