# Email Automation — Envoi par dossiers

Application Python pour l'envoi automatisé d'e-mails personnalisés à partir d'une arborescence de dossiers.


## Installation

```bash
git clone <repo>
cd email_automation

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env
# → Éditez .env avec vos identifiants SMTP
```

---

## 🗂️ Structure des dossiers

```
emails/
├── client_A/
│   ├── config.json       ← obligatoire
│   ├── test.txt
└── client_B/
    ├── config.json
    └── rapport.xlsx
```

### Format `config.json`

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
