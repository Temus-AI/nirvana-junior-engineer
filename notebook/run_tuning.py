from optm.soft_prompt import *
from runs.config import *
import logging
from datetime import datetime
import hydra
from omegaconf import DictConfig
import os

# Set up logging with explicit path
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f"tuning_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@hydra.main(config_path="runs/conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:

    hydra.core.hydra_config.HydraConfig.get().set_config({
        "hydra": {
            "job": {"chdir": False}  # Keep working directory at project root
        }
    })
    
    # Form config dict with only the required fields
    config_dict = {
        "num_virtual_tokens": cfg.num_virtual_tokens,
        "token_dim": cfg.token_dim,
        "num_attention_heads": cfg.num_attention_heads,
        "num_layers": cfg.num_layers,
        "model_name": cfg.model_name,
        "prompt_tuning_init_text": cfg.prompt_tuning_init_text,
        "config_id": cfg.config_id,
        "batch_size": cfg.batch_size,
        "accumulation_steps": cfg.accumulation_steps
    }
    
    if cfg.prompt_tuning:
        logging.info(f"Starting {config_dict['config_id']} prompt tuning...")
        try:
            run_prompt_tuning_pipeline(config_dict, cfg.num_epochs, cfg.learning_rate)
        except Exception as e:
            error_msg = f"Error running {config_dict['config_id']} prompt tuning: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
    
    if cfg.token_tuning:
        logging.info(f"Starting {config_dict['config_id']} token tuning...")
        try:
            run_token_tuning_pipeline(config_dict, cfg.num_epochs, cfg.learning_rate)
        except Exception as e:
            error_msg = f"Error running {config_dict['config_id']} token tuning: {str(e)}"
            print(error_msg)
            logging.error(error_msg)

if __name__ == "__main__":
    main()
    # Example Command: 
    # python run_tuning.py model=qwen7B lr=3e-4 num_epochs=5