python run_tuning.py model=unsloth/Meta-Llama-3.1-8B-Instruct lr=3e-3 num_epochs=5 token_tuning=true prompt_tuning=false reft=false config_id=llama8b_5 accumulation_steps=64
python run_tuning.py model=unsloth/Meta-Llama-3.1-8B-Instruct lr=3e-3 num_epochs=20 token_tuning=true prompt_tuning=false reft=false config_id=llama8b_6 accumulation_steps=128
python run_tuning.py model=unsloth/Llama-3.2-1B-Instruct lr=3e-3 num_epochs=5 token_tuning=true prompt_tuning=false reft=false config_id=llama1b_1 accumulation_steps=128
python run_tuning.py model=unsloth/Llama-3.2-1B-Instruct lr=3e-3 num_epochs=20 token_tuning=true prompt_tuning=false reft=false config_id=llama1b_2 accumulation_steps=128
python run_tuning.py model=HuggingFaceTB/SmolLM2-1.7B-Instruct lr=3e-3 num_epochs=5 token_tuning=true prompt_tuning=false reft=false config_id=smol1b_1 accumulation_steps=128
python run_tuning.py model=HuggingFaceTB/SmolLM2-1.7B-Instruct lr=3e-3 num_epochs=20 token_tuning=true prompt_tuning=false reft=false config_id=smol1b_2 accumulation_steps=128