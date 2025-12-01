#lichessLLMAPI.py
import os
import requests
from typing import Optional

class LichessLLMAPI:
    """
    Lekki klient do pobierania PGN i danych gier z Lichess
    przeznaczony do integracji z LLM / RAG.
    """

    def __init__(self, token: Optional[str] = None, timeout: int = 30):
        self.base_url = "https://lichess.org"
        self.timeout = timeout
        self.token = token or os.getenv("LICHESS_API_TOKEN", None)

        self.headers = {
            "Accept": "application/x-chess-pgn",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    # ------------------------------------------
    # Pobieranie pojedynczej gry w PGN
    # ------------------------------------------
    def get_game_pgn(self, game_id: str) -> str:
        url = f"{self.base_url}/game/export/{game_id}.pgn"
        response = requests.get(url, headers=self.headers, timeout=self.timeout)

        if response.status_code == 200:
            return response.text
        else:
            raise Exception(
                f"Błąd pobierania PGN: HTTP {response.status_code}. Treść: {response.text}"
            )

    # ------------------------------------------
    # Pobieranie wielu gier użytkownika
    # ------------------------------------------
    def get_user_games(self, username: str, max_games: int = 20) -> str:
        url = f"{self.base_url}/api/games/user/{username}?max={max_games}&pgnInJson=true"
        headers = dict(self.headers)
        headers["Accept"] = "application/x-ndjson"

        response = requests.get(url, headers=headers, timeout=self.timeout)

        if response.status_code == 200:
            return response.text
        else:
            raise Exception(
                f"Błąd pobierania gier użytkownika: HTTP {response.status_code}. Treść: {response.text}"
            )

    # ------------------------------------------
    # Sprawdzenie tokena
    # ------------------------------------------
    def verify_token(self):
        url = f"{self.base_url}/api/account"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.get(url, headers=headers, timeout=self.timeout)
        return response.status_code, response.text


if __name__ == "__main__":
    api = LichessLLMAPI(token="TU_WKLEJ_TOKEN")

    # Test
    print(api.verify_token())