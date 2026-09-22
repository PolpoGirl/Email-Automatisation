"""
Gestion de la configuration via .env / variables d'environnement
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """Centralise toute la configuration de l'application."""

    def __init__(self):
        # SMTP
        self.smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user: str = os.getenv("SMTP_USER", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        # Expéditeur
        self.sender_name: str = os.getenv("SENDER_NAME", "")
        self.sender_email: str = os.getenv("SENDER_EMAIL", self.smtp_user)

        # Chemins
        self.emails_dir: Path = Path(os.getenv("EMAILS_DIR", "emails"))
        self.template_path: Path = Path(
            os.getenv("TEMPLATE_PATH", "templates/default.html")
        )
        self.log_file: Path = Path(os.getenv("LOG_FILE", "logs/envois.log"))
        self.csv_log_file: Path = Path(os.getenv("CSV_LOG_FILE", "logs/envois.csv"))

        # Limites
        self.rate_limit_delay: float = float(os.getenv("RATE_LIMIT_DELAY", "2.0"))  # secondes entre envois
        self.max_attachment_size_mb: int = int(
            os.getenv("MAX_ATTACHMENT_SIZE_MB", "25")
        )

    def validate(self) -> list[str]:
        """Retourne la liste des erreurs de configuration."""
        errors = []
        if not self.smtp_host:
            errors.append("SMTP_HOST manquant")
        if not self.smtp_user:
            errors.append("SMTP_USER manquant")
        if not self.smtp_password:
            errors.append("SMTP_PASSWORD manquant")
        return errors
