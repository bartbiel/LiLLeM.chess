# LiLLeM.chess
<h2>Tool for chess game analysis</h2>
<h3>Some statistics</h3>
<br>Integration with lichess API for:
<ul>
<li>rapid</li>
<li>blitz</li>
<li>bullet</li>
</ul>
<br>Example CPL evaluation
<img src="./plots/CPL_https___lichess_org_wCBOmLIY.png">
<br>Trend history accross last 50 games
<img src="./plots/largeTrend.png">
<br>Top blunders from last games
<img src="./plots/topBlunders.png">
<br>Heatmaps example
<img src="./plots/heatmaps/blunders.png">
<img src="./plots/heatmaps/cpl_heatmap.png">
<img src="./plots/heatmaps/move_frequency.png">
<h3> LLM for a game analysis</h3>
<br>Dependencies
<br>pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
<br>pip install transformers accelerate einops safetensors sentencepiece huggingface_hub
<br>pip install python-chess
<br>pip install matplotlib
<br>pip install seaborn
<br>pip install langchain faiss-cpu sentence-transformers
<br>pip install langchain langchain-community langchain-core
<br>pip install faiss-cpu
<br>pip install protobuf google

<br>
<br><b>Important! - </b>run_llm_game_by_id , for instance: python run_llm_game_by_id.py last [username]
<br>In my case: python run_llm_game_by_id.py last bielbart77







