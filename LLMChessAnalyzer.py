import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class LLMChessAnalyzer:
    """
    Klasa odpowiedzialna za tworzenie podsumowania partii szachowej
    z wykorzystaniem lokalnego modelu Mistral / HuggingFace.
    """

    def __init__(self, mistral_snapshot_path: str, device: str = "cpu"):
        print(f"[LLMChessAnalyzer] Ładowanie modelu z: {mistral_snapshot_path}")

        self.device = device

        # Ładowanie modelu
        self.tokenizer = AutoTokenizer.from_pretrained(mistral_snapshot_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            mistral_snapshot_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None
        )

        print("[LLMChessAnalyzer] Model poprawnie załadowany.\n")

    # ---------------------------------------------------------------------

    def summarize_game(self, analysis_obj):
        """
        Przyjmuje obiekt GameAnalysisResult lub słownik.
        Zamienia obiekt na dict i generuje prompt dla LLM.
        """

        # Zamiana obiektu na słownik jeśli trzeba
        if hasattr(analysis_obj, "__dict__"):
            data = analysis_obj.__dict__
        else:
            data = analysis_obj

        print("\n===== GENERATING LLM ANALYSIS =====\n")

        prompt = self._build_prompt(data)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        output = self.model.generate(
            **inputs,
            max_new_tokens=600,
            temperature=0.3,
            do_sample=True
        )

        full_text = self.tokenizer.decode(output[0], skip_special_tokens=True)

        # Usuń prompt z odpowiedzi
        result = full_text[len(prompt):].strip()
        return result

    # ---------------------------------------------------------------------

    def _build_prompt(self, data: dict):
        """
        Buduje prompt dla LLM na podstawie danych analitycznych.
        """

        moves = " ".join(data.get("moves", []))
        winner = data.get("winner", "unknown")
        termination = data.get("termination", "unknown")
        white = data.get("white", "White")
        black = data.get("black", "Black")

        # Jeśli było otwarcie z Lichess
        opening_name = data.get("opening_name", "unknown")
        opening_ecos = data.get("opening_eco", "")

        prompt = f"""
Jesteś ekspertem szachowym. Na podstawie podanych danych wygeneruj wyczerpującą,
czytelną analizę partii: omów otwarcie, plan obu stron, kluczowe momenty oraz błędy.

Dane partii:
- Białe: {white}
- Czarne: {black}
- Zwycięzca: {winner}
- Sposób zakończenia: {termination}
- Otwarcie: {opening_name} ({opening_ecos})

Lista ruchów (PGN moves):
{moves}

Stwórz szczegółową analizę w języku polskim.
"""

        return prompt
