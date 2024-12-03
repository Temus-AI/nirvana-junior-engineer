from optm.soft_prompt import *
from runs.config import *
import logging
from datetime import datetime

# Set up logging
log_filename = f"tuning_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

config_dicts = [qwen_05_config_dict, qwen_7_config_dict, llama_3_8b_config_dict]

for config_dict in config_dicts:
    logging.info(f"Starting {config_dict['config_id']} prompt tuning...")
    try:
        run_prompt_tuning_pipeline(config_dict, num_epochs=50, learning_rate=3e-4, device="cuda")
    except Exception as e:
        error_msg = f"Error running {config_dict['config_id']} prompt tuning: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
    
    logging.info(f"Starting {config_dict['config_id']} token tuning...")
    try:
        run_token_tuning_pipeline(config_dict, num_epochs=50, learning_rate=3e-4, device="cuda")
    except Exception as e:
        error_msg = f"Error running {config_dict['config_id']} token tuning: {str(e)}"
        print(error_msg)
        logging.error(error_msg)