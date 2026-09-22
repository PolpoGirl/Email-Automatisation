"""
Scan du répertoire racine et chargement des dossiers valides
"""

import json
import re
import logging
from pathlib import Path
from dataclasses import dataclass, field


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class DossierEmail:
    """Représente un dossier e-mail prêt à l'envoi."""
    nom: str
    chemin: Path
    destinataire: str
    sujet: str
    variables: dict
    cc: list[str] = field(default_factory=list)
    cci: list[str] = field(default_factory=list)
    pieces_jointes: list[Path] = field(default_factory=list)


class FolderScanner:
    """Scanne un répertoire et retourne les dossiers e-mail valides."""

    def __init__(self, racine: Path, logger: logging.Logger):
        self.racine = racine
        self.logger = logger

    def scan(self, retry_failed_only: bool = False) -> list[DossierEmail]:
        """
        Parcourt tous les sous-dossiers et retourne les dossiers valides.
        Si retry_failed_only=True, ne retourne que ceux marqués ECHEC dans le log CSV.
        """
        dossiers = []
        failed_names = self._get_failed_names() if retry_failed_only else None

        for entry in sorted(self.racine.iterdir()):
            if not entry.is_dir():
                continue

            config_path = entry / "config.json"
            if not config_path.exists():
                self.logger.warning(f"[{entry.name}] Ignoré — config.json absent")
                continue

            if failed_names is not None and entry.name not in failed_names:
                continue

            dossier = self._charger_dossier(entry, config_path)
            if dossier:
                dossiers.append(dossier)

        return dossiers

    def _charger_dossier(self, chemin: Path, config_path: Path) -> DossierEmail | None:
        """Charge et valide un dossier e-mail."""
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"[{chemin.name}] config.json invalide : {e}")
            return None

        # Champs obligatoires
        for champ in ("destinataire", "sujet"):
            if champ not in cfg:
                self.logger.error(f"[{chemin.name}] Champ manquant : '{champ}'")
                return None

        # Validation adresse e-mail
        dest = cfg["destinataire"].strip()
        if not EMAIL_REGEX.match(dest):
            self.logger.error(f"[{chemin.name}] Adresse invalide : {dest}")
            return None

        # Validation CC
        cc_list = cfg.get("cc", [])
        cci_list = cfg.get("cci", [])
        cc_valides = [a for a in cc_list if EMAIL_REGEX.match(a.strip())]
        cci_valides = [a for a in cci_list if EMAIL_REGEX.match(a.strip())]

        invalides_cc = set(cc_list) - set(cc_valides)
        if invalides_cc:
            self.logger.warning(f"[{chemin.name}] CC ignorés (invalides) : {invalides_cc}")

        # Pièces jointes (tout fichier sauf config.json)
        pieces = [
            f for f in chemin.iterdir()
            if f.is_file() and f.name != "config.json"
        ]

        return DossierEmail(
            nom=chemin.name,
            chemin=chemin,
            destinataire=dest,
            sujet=cfg["sujet"],
            variables=cfg.get("variables", {}),
            cc=cc_valides,
            cci=cci_valides,
            pieces_jointes=sorted(pieces),
        )

    def _get_failed_names(self) -> set[str]:
        """Lit le CSV de log et retourne les noms des dossiers en échec."""
        from pathlib import Path
        import csv

        csv_path = Path("logs/envois.csv")
        if not csv_path.exists():
            return set()

        failed = set()
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("statut", "").upper() == "ECHEC":
                    failed.add(row.get("dossier", ""))
        return failed
