from optm.soft_prompt import *
from runs.config import *
import logging
from datetime import datetime
import hydra
from omegaconf import DictConfig

# Set up logging
log_filename = f"tuning_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@hydra.main(config_path="runs/conf", config_name="config")
def main(cfg: DictConfig):
    # Get the model config based on the model name
    model_configs = {
        "qwen0.5B": qwen_05_config_dict,
        "qwen7B": qwen_7_config_dict,
        "llama3.8B": llama_3_8b_config_dict
    }
    
    config_dict = model_configs[cfg.model]
    
    if cfg.prompt_tuning:
        logging.info(f"Starting {config_dict['config_id']} prompt tuning...")
        try:
            run_prompt_tuning_pipeline(
                config_dict, 
                num_epochs=cfg.num_epochs, 
                learning_rate=cfg.lr, 
                device=cfg.device
            )
        except Exception as e:
            error_msg = f"Error running {config_dict['config_id']} prompt tuning: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
    
    if cfg.token_tuning:
        logging.info(f"Starting {config_dict['config_id']} token tuning...")
        try:
            run_token_tuning_pipeline(
                config_dict, 
                num_epochs=cfg.num_epochs, 
                learning_rate=cfg.lr, 
                device=cfg.device
            )
        except Exception as e:
            error_msg = f"Error running {config_dict['config_id']} token tuning: {str(e)}"
            print(error_msg)
            logging.error(error_msg)

if __name__ == "__main__":
    main()