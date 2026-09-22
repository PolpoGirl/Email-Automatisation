"""
Application d'automatisation d'envoi d'e-mails par dossiers
Point d'entrée principal
"""

import argparse
import sys
from pathlib import Path
from core.scanner import FolderScanner
from core.sender import EmailSender
from core.logger import setup_logger
from core.config import AppConfig


def main():
    parser = argparse.ArgumentParser(
        description="Automatisation d'envoi d'e-mails par dossiers"
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Répertoire racine contenant les dossiers e-mails (override .env)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode test : analyse sans envoyer"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Relancer uniquement les envois en échec"
    )
    parser.add_argument(
        "--template",
        type=str,
        help="Chemin vers le fichier template Jinja2 (override .env)"
    )

    args = parser.parse_args()

    # Chargement config
    config = AppConfig()
    logger = setup_logger(config.log_file)

    emails_dir = Path(args.dir) if args.dir else config.emails_dir
    template_path = Path(args.template) if args.template else config.template_path

    if not emails_dir.exists():
        logger.error(f"Répertoire introuvable : {emails_dir}")
        sys.exit(1)

    if not template_path.exists():
        logger.error(f"Template introuvable : {template_path}")
        sys.exit(1)

    mode = "DRY-RUN" if args.dry_run else "ENVOI RÉEL"
    logger.info(f"=== Démarrage — Mode : {mode} ===")
    logger.info(f"Répertoire : {emails_dir}")
    logger.info(f"Template   : {template_path}")

    # Scan des dossiers
    scanner = FolderScanner(emails_dir, logger)
    dossiers = scanner.scan(retry_failed_only=args.retry_failed)

    if not dossiers:
        logger.info("Aucun dossier valide trouvé. Fin.")
        return

    logger.info(f"{len(dossiers)} dossier(s) à traiter.")

    # Envoi
    sender = EmailSender(config, template_path, logger, dry_run=args.dry_run)
    sender.process_all(dossiers)

    logger.info("=== Terminé ===")


if __name__ == "__main__":
    main()
