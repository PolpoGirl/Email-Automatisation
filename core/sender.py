"""
Moteur d'envoi d'e-mails : rendu template + SMTP + pièces jointes
"""

import smtplib
import time
import logging
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from core.config import AppConfig
from core.scanner import DossierEmail
from core.logger import CsvLogger


class EmailSender:
    """Gère le rendu des templates et l'envoi SMTP."""

    def __init__(
        self,
        config: AppConfig,
        template_path: Path,
        logger: logging.Logger,
        dry_run: bool = False,
    ):
        self.config = config
        self.template_path = template_path
        self.logger = logger
        self.dry_run = dry_run
        self.csv_logger = CsvLogger(config.csv_log_file)

        # Chargement environnement Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=True,
        )

    def process_all(self, dossiers: list[DossierEmail]):
        """Traite tous les dossiers un par un avec rate limiting."""
        succes, echecs = 0, 0

        for i, dossier in enumerate(dossiers):
            ok = self._process_one(dossier)
            if ok:
                succes += 1
            else:
                echecs += 1

            # Rate limiting (sauf après le dernier)
            if not self.dry_run and i < len(dossiers) - 1:
                time.sleep(self.config.rate_limit_delay)

        self.logger.info(
            f"Résultat : {succes} succès, {echecs} échec(s) sur {len(dossiers)}"
        )

    def _process_one(self, dossier: DossierEmail) -> bool:
        """Traite un dossier : rendu + envoi."""
        self.logger.info(f"[{dossier.nom}] → {dossier.destinataire}")

        # Rendu du template
        try:
            corps = self._render_template(dossier.variables)
        except Exception as e:
            self.logger.error(f"[{dossier.nom}] Erreur template : {e}")
            self.csv_logger.log(dossier, "ECHEC", str(e))
            return False

        # Vérification pièces jointes
        for pj in dossier.pieces_jointes:
            taille_mb = pj.stat().st_size / (1024 * 1024)
            if taille_mb > self.config.max_attachment_size_mb:
                msg = f"PJ trop lourde ({taille_mb:.1f} MB) : {pj.name}"
                self.logger.error(f"[{dossier.nom}] {msg}")
                self.csv_logger.log(dossier, "ECHEC", msg)
                return False

        if self.dry_run:
            self.logger.info(
                f"[{dossier.nom}] DRY-RUN — sujet: '{dossier.sujet}' | "
                f"PJ: {[p.name for p in dossier.pieces_jointes]}"
            )
            self.csv_logger.log(dossier, "DRY-RUN")
            return True

        # Construction du message MIME
        msg = self._build_message(dossier, corps)

        # Envoi SMTP
        try:
            self._send_smtp(msg, dossier)
            self.logger.info(f"[{dossier.nom}] ✓ Envoyé")
            self.csv_logger.log(dossier, "SUCCES")
            return True
        except smtplib.SMTPRecipientsRefused as e:
            msg_err = f"Destinataire refusé : {e}"
            self.logger.error(f"[{dossier.nom}] {msg_err}")
            self.csv_logger.log(dossier, "ECHEC", msg_err)
            return False
        except smtplib.SMTPAuthenticationError:
            msg_err = "Authentification SMTP échouée"
            self.logger.error(f"[{dossier.nom}] {msg_err}")
            self.csv_logger.log(dossier, "ECHEC", msg_err)
            return False
        except Exception as e:
            self.logger.error(f"[{dossier.nom}] Erreur SMTP : {e}")
            self.csv_logger.log(dossier, "ECHEC", str(e))
            return False

    def _render_template(self, variables: dict) -> str:
        """Rend le template Jinja2 avec les variables fournies."""
        try:
            tpl = self.jinja_env.get_template(self.template_path.name)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template introuvable : {self.template_path.name}")
        return tpl.render(**variables)

    def _build_message(self, dossier: DossierEmail, corps: str) -> MIMEMultipart:
        """Construit le message MIME complet."""
        msg = MIMEMultipart("mixed")

        expediteur = (
            f"{self.config.sender_name} <{self.config.sender_email}>"
            if self.config.sender_name
            else self.config.sender_email
        )
        msg["From"] = expediteur
        msg["To"] = dossier.destinataire
        msg["Subject"] = dossier.sujet

        if dossier.cc:
            msg["Cc"] = ", ".join(dossier.cc)
        if dossier.cci:
            msg["Bcc"] = ", ".join(dossier.cci)

        # Corps HTML ou texte selon l'extension du template
        content_type = (
            "html" if self.template_path.suffix.lower() in (".html", ".htm") else "plain"
        )
        msg.attach(MIMEText(corps, content_type, "utf-8"))

        # Pièces jointes
        for pj in dossier.pieces_jointes:
            self._attach_file(msg, pj)

        return msg

    def _attach_file(self, msg: MIMEMultipart, path: Path):
        """Ajoute un fichier en pièce jointe."""
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"

        with open(path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=path.name,
        )
        msg.attach(part)

    def _send_smtp(self, msg: MIMEMultipart, dossier: DossierEmail):
        """Connexion SMTP et envoi."""
        all_recipients = (
            [dossier.destinataire] + dossier.cc + dossier.cci
        )

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            server.ehlo()
            if self.config.smtp_use_tls:
                server.starttls()
                server.ehlo()
            server.login(self.config.smtp_user, self.config.smtp_password)
            server.sendmail(
                self.config.sender_email,
                all_recipients,
                msg.as_string(),
            )
