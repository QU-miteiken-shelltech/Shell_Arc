import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

from shellarc_core.exception.structure_error import SA_AuthError, SA_ErrorCode


class AccessDB:
    def __init__(self):
        load_dotenv(verbose=True)
        project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
        dotenv_path = project_ctx_dir / ".env"
        if not dotenv_path.exists():
            raise SA_AuthError(
                error_log=f"dotenv_path {dotenv_path} not exist",
                error_code=SA_ErrorCode.SA_9001
            )
        load_dotenv(dotenv_path)
        service_account_info = {
            "type": os.environ.get("firebase_type"),
            "project_id": os.environ.get("firebase_project_id"),
            "private_key_id": os.environ.get("firebase_private_key_id"),
            "private_key": os.environ.get("firebase_private_key").replace('\\n', '\n'),
            "client_email": os.environ.get("firebase_client_email"),
            "client_id": os.environ.get("firebase_client_id"),
            "auth_uri": os.environ.get("firebase_auth_uri"),
            "token_uri": os.environ.get("firebase_token_uri"),
            "auth_provider_x509_cert_url": os.environ.get("firebase_auth_provider_x509_cert_url"),
            "client_x509_cert_url": os.environ.get("firebase_client_x509_cert_url"),
            "universe_domain": os.environ.get("firebase_universe_domain")   
        }
        cred = credentials.Certificate(service_account_info)
        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self._database = firestore.client()
        except Exception as e:
            self._database = None
            raise SA_AuthError(
                error_log=f"Auth error in Firebase [{e}]",
                error_code=SA_ErrorCode.SA_9000
            )

    @property
    def database(self) -> firestore.Client:
        """Get the Firestore client instance (Property)

        Returns:
            _database (firestore.Client): The Firestore client instance for database operations.
        """
        return self._database


