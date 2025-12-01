# lichessAPI.py
import requests
from dataclasses import dataclass
import json
from typing import List, Optional


@dataclass
class LichessGame:
    game_id: str
    pgn: str



class LichessClient:
    def __init__(self, token: Optional[str] = None, timeout: int = 30):
        self.base_url = "https://lichess.org/api"
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/x-ndjson"})  # <-- KLUCZOWE
        self.timeout = timeout
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_user_games(
        self,
        username: str,
        max_games: int = 20,
        perf_type: Optional[str] = None,
        rated: Optional[bool] = None,
    ) -> List[LichessGame]:
        """
        Pobiera partie użytkownika z Lichess jako NDJSON stream.
        Zwraca listę obiektów LichessGame.
        Implementacja używa buforowego parsowania: łączy przychodzące chunki,
        dzieli po '\n' i parsuje tylko kompletne linie JSON.
        """

        url = f"{self.base_url}/games/user/{username}"

        params = {
            "max": max_games,
            "pgnInJson": True,
        }

        if perf_type:
            params["perfType"] = perf_type

        if rated is not None:
            params["rated"] = "true" if rated else "false"

        resp = self.session.get(url, params=params, stream=True, timeout=self.timeout)

        if resp.status_code != 200:
            raise RuntimeError(f"Lichess API returned status {resp.status_code}: {resp.text[:300]}")

        games: List[LichessGame] = []
        buffer = ""  # tekstowy buffer do składania chunków

        # iter_content gwarantuje nam odbieranie chunków (mogą zawierać wiele linii
        # lub fragmenty linii) — z nimi radzimy sobie poniżej
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                continue
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8", errors="ignore")
            buffer += chunk

            # rozbijamy na kompletne linie
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                text = line.strip()
                if not text:
                    continue
                # często Lichess zwraca NDJSON (pojedynczy JSON na linię)
                # upewniamy się, że linia wygląda jak JSON
                if not text.startswith("{"):
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError:
                    # pominąć niepoprawne linie (mogą to być fragmenty)
                    continue

                game_id = obj.get("id", "unknown")
                pgn = obj.get("pgn", "")
                games.append(LichessGame(game_id=game_id, pgn=pgn))

        # Po zakończeniu pętli może zostać nieprzetworzony fragment w buffer
        tail = buffer.strip()
        if tail and tail.startswith("{"):
            try:
                obj = json.loads(tail)
                game_id = obj.get("id", "unknown")
                pgn = obj.get("pgn", "")
                games.append(LichessGame(game_id=game_id, pgn=pgn))
            except json.JSONDecodeError:
                # ignorujemy niekompletny tail
                pass

        return games
