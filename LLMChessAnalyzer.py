import io
import chess
import chess.pgn
from stockfish import Stockfish
from transformers import AutoTokenizer, AutoModelForCausalLM


class LLMChessAnalyzer:
    def __init__(self, model_path: str, stockfish_path: str = "stockfish.exe"):
        print("[LLMChessAnalyzer] Loading model...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            dtype="auto",
        )
        print("[LLMChessAnalyzer] Model loaded successfully.")

        self.stockfish = Stockfish(
            path=stockfish_path,
            depth=18,
            parameters={"Threads": 4, "Minimum Thinking Time": 30}
        )
        print("[LLMChessAnalyzer] Stockfish initialized.")

    # -----------------------------------------------------

    def parse_pgn_moves(self, pgn_text):
        """
        Parse PGN and return two lists:
          - moves_san: ["e4", "e5", "Nf3", ...]
          - moves_uci: ["e2e4", "e7e5", "g1f3", ...]
        """
        pgn = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn)
        if not game:
            return [], []

        board = game.board()

        moves_san = []
        moves_uci = []

        for move in game.mainline_moves():
            san = board.san(move)
            uci = move.uci()

            moves_san.append(san)
            moves_uci.append(uci)

            board.push(move)

        return moves_san, moves_uci

    # -----------------------------------------------------

    def _score_from_eval(self, eval_data):
        """
        Convert stockfish.get_evaluation() return value to centipawns integer.
        If mate -> large positive/negative sentinel.
        """
        if not isinstance(eval_data, dict):
            return 0
        t = eval_data.get("type")
        v = eval_data.get("value", 0)
        if t == "cp":
            return int(v)
        elif t == "mate":
            # mate in N => represent as large score; sign preserved
            # positive v -> mate for white, negative -> mate for black
            # use large magnitude to outrank cp values
            return 100000 if v > 0 else -100000
        else:
            return 0

    # -----------------------------------------------------

    def find_worst_moves(self, moves_san, n=2):
        """
        Finds the N worst moves based on Stockfish evaluation drop.
        Returns list of tuples: (move_number (1-based ply pair index), san, loss)
          e.g. [(13, "Nd4", -466), (59, "Ke3", -278)]
        moves_san should be a list of SAN strings in game order (white, black, white, ...).
        """
        board = chess.Board()
        records = []  # tuples of (move_index, san, loss)

        # We'll track evaluation before the move and after the move for each ply.
        # Use Stockfish by setting fen to board.fen() before and after move.
        eval_before = None

        for ply_idx, move_san in enumerate(moves_san):
            # evaluation before move (from the current board)
            fen_before = board.fen()
            try:
                self.stockfish.set_fen_position(fen_before)
            except Exception:
                # fallback: use set_position([]) if wrapper does not accept fen (unlikely)
                try:
                    self.stockfish.set_position([])
                except Exception:
                    pass

            eval_data_before = self.stockfish.get_evaluation()
            val_before = self._score_from_eval(eval_data_before)

            # parse and push the move on python-chess board
            try:
                move = board.parse_san(move_san)
            except Exception:
                # warn and skip this ply if parsing fails
                print(f"[WARN] Could not parse SAN move: {move_san}")
                # still attempt to continue (do not push)
                continue

            board.push(move)

            # evaluation after move (on new board)
            fen_after = board.fen()
            try:
                self.stockfish.set_fen_position(fen_after)
            except Exception:
                try:
                    self.stockfish.set_position([])
                except Exception:
                    pass

            eval_data_after = self.stockfish.get_evaluation()
            val_after = self._score_from_eval(eval_data_after)

            # loss: after - before (negative = evaluation dropped for side to move BEFORE move)
            # Note: because evaluations are from white's perspective, sign already reflects advantage.
            loss = val_after - val_before

            # Convert ply_idx to human move number:
            # ply_idx=0 -> move 1 (white), ply_idx=1 -> move 1 (black), ply_idx=2 -> move 2 (white), ...
            move_number = (ply_idx // 2) + 1

            records.append((move_number, move_san, loss))

        # sort by loss (most negative first)
        records.sort(key=lambda x: x[2])

        # return top n worst
        return records[:n]

    # -----------------------------------------------------

    def ask_llm(self, bad_moves):
        """
        bad_moves: list of tuples (move_number, san, loss)
        Example: [(13, "Nd4", -466), (59, "Ke3", -278)]
        """
        prompt = "You are a chess expert. Explain why the following moves were bad.\n"
        prompt += "For each move provide concise tactical/strategic reasons and avoid hallucination.\n\n"

        for num, san, drop in bad_moves:
            prompt += f"- Move {num}: {san} (eval change: {drop})\n"

        prompt += "\nExplain concisely and base the explanation on standard chess principles."

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        output = self.model.generate(**inputs, max_new_tokens=350)
        text = self.tokenizer.decode(output[0], skip_special_tokens=True)

        # strip the prompt if included
        return text.replace(prompt, "").strip()

    # -----------------------------------------------------

    def analyze_game(self, pgn_text: str, n_worst: int = 2):
        """
        Full game analysis:
        1. Extract SAN + UCI moves from PGN
        2. Evaluate moves using Stockfish to find the N worst moves
        3. Ask LLM to explain them
        Returns dict with keys:
          - worst_moves: list of (move_number, san, loss)
          - analysis: LLM text
        """
        moves_san, moves_uci = self.parse_pgn_moves(pgn_text)

        if not moves_san:
            return {
                "worst_moves": [],
                "analysis": "Error: Could not parse PGN moves."
            }

        worst = self.find_worst_moves(moves_san, n=n_worst)
        explanation = self.ask_llm(worst) if worst else "No bad moves found."

        return {
            "worst_moves": worst,
            "analysis": explanation
        }
