from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_server: str = r"localhost\SQLEXPRESS"
    db_name: str = "DS_Votaciones"
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_trusted_connection: bool = True
    db_user: str = ""
    db_password: str = ""
    db_encrypt: str = "yes"
    db_trust_server_certificate: str = "yes"

    @property
    def sqlalchemy_url(self) -> str:
        odbc = (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER={self.db_server};"
            f"DATABASE={self.db_name};"
            f"Encrypt={self.db_encrypt};"
            f"TrustServerCertificate={self.db_trust_server_certificate};"
        )
        if self.db_trusted_connection:
            odbc += "Trusted_Connection=yes;"
        else:
            odbc += f"UID={self.db_user};PWD={self.db_password};"

        from urllib.parse import quote_plus

        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"


settings = Settings()
