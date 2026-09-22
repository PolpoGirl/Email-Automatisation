"""
Journalisation : fichier .log + CSV horodaté
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

from core.scanner import DossierEmail


def setup_logger(log_file: Path) -> logging.Logger:
    """Configure et retourne le logger principal."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("email_automation")
    logger.setLevel(logging.DEBUG)

    # Évite les doublons si appelé plusieurs fois
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler fichier
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Handler console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


class CsvLogger:
    """Enregistre chaque envoi dans un fichier CSV."""

    HEADERS = ["horodatage", "dossier", "destinataire", "sujet", "statut", "erreur"]

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_file()

    def _init_file(self):
        """Crée le fichier CSV avec en-têtes s'il n'existe pas."""
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS)
                writer.writeheader()

    def log(self, dossier: DossierEmail, statut: str, erreur: str = ""):
        """Ajoute une ligne au CSV."""
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADERS)
            writer.writerow({
                "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "dossier": dossier.nom,
                "destinataire": dossier.destinataire,
                "sujet": dossier.sujet,
                "statut": statut,
                "erreur": erreur,
            })
