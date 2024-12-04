from optm.soft_prompt import load_tf_data, _form_query, _form_response, load_hf_model_precise, RUN_DIR
import pyreft, transformers
from pyreft import ReftTrainerForCausalLM


# Loading moded
def load_reft_model(model_name): 
    
    model_name = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
    model, tokenizer = load_hf_model_precise(model_name) # load model & tokenizer
    tokenizer = transformers.AutoTokenizer.from_pretrained(
                model_name, model_max_length=4096, 
                padding_side="right", use_fast=False)
    tokenizer.pad_token = tokenizer.unk_token


    reft_config = pyreft.ReftConfig(representations={
        "layer": 8, "component": "block_output",
        "low_rank_dimension": 4,
        "intervention": pyreft.LoreftIntervention(embed_dim=model.config.hidden_size,
        low_rank_dimension=4)})

    reft_model = pyreft.get_reft_model(model, reft_config)
    reft_model.set_device("cuda")
    reft_model.print_trainable_parameters()
    
    return reft_model, tokenizer


def prepare_reft_training_examples(tokenizer):
    msg = [{"role": "system", "content": "SYSTEM_CONTENT"}, {"role": "user", "content": "%s"}, {"role": "assistant", "content": "ASSISTANT_CONTENT"}]
    default_template = tokenizer.apply_chat_template(msg, tokenize=False)
    prompt_no_input_template = ("").join(default_template.split(tokenizer.eos_token)[1:]).split("ASSISTANT_CONTENT")[0]
    response_no_input_template = "%s" + default_template.split("ASSISTANT_CONTENT")[1]
    
    prompt_no_input_template, response_no_input_template
    
    train_set, test_set = load_tf_data()
    
    training_examples = []
    for prompt, label, comment in zip(train_set["prompt"], train_set["label"], train_set["comment"]):
        query_str = _form_query(prompt)
        response_str = _form_response(label, comment) 
        query = prompt_no_input_template % query_str
        response = response_no_input_template % response_str
        training_examples.append(tuple([query, response]))

    return training_examples 

def train_reft_model(reft_model, training_examples, tokenizer, train_config: dict):
    
    data_module = pyreft.make_last_position_supervised_data_module(
        tokenizer, reft_model, [e[0] for e in training_examples], # Used to be 'model' but replace with 'reft_model' 
        [e[1] for e in training_examples])
    
    
    training_args = transformers.TrainingArguments(
    num_train_epochs=train_config.get("num_epochs", 10.0), output_dir=RUN_DIR, per_device_train_batch_size=10, 
    learning_rate=train_config.get("lr", 4e-3), logging_steps=2, report_to=[])

    class CustomReftTrainer(ReftTrainerForCausalLM):
        def compute_loss(self, model, inputs, *args, **kwargs):
            # Ignore the num_items_in_batch argument
            return super().compute_loss(model, inputs)

    trainer = CustomReftTrainer(
        model=reft_model, tokenizer=tokenizer, args=training_args, **data_module)

    _ = trainer.train()