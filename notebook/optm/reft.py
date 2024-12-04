from optm.soft_prompt import load_tf_data, _form_query, _form_response, load_hf_model_precise, RUN_DIR
import pyreft, transformers
from pyreft import ReftTrainerForCausalLM
import torch


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


def prepare_reft_training_examples(tokenizer, use_train: bool = True):
    msg = [{"role": "system", "content": "SYSTEM_CONTENT"}, {"role": "user", "content": "%s"}, {"role": "assistant", "content": "ASSISTANT_CONTENT"}]
    default_template = tokenizer.apply_chat_template(msg, tokenize=False)
    prompt_no_input_template = ("").join(default_template.split(tokenizer.eos_token)[1:]).split("ASSISTANT_CONTENT")[0]
    response_no_input_template = "%s" + default_template.split("ASSISTANT_CONTENT")[1]
    
    prompt_no_input_template, response_no_input_template
    
    train_set, test_set = load_tf_data()
    
    from optm.soft_prompt import _form_query, _form_response
    
    training_examples = []
    for prompt, label, comment in zip(train_set["prompt"], train_set["label"], train_set["comment"]):
        query_str = _form_query(prompt)
        response_str = _form_response(label, comment) 
        query = prompt_no_input_template % query_str
        response = response_no_input_template % response_str
        training_examples.append(tuple([query, response]))

    testing_examples = []
    for prompt, label, comment in zip(test_set["prompt"], test_set["label"], test_set["comment"]):
        query_str = _form_query(prompt)
        response_str = _form_response(label, comment) 
        query = prompt_no_input_template % query_str
        response = response_no_input_template % response_str
        testing_examples.append(tuple([query, response]))
    
    return training_examples, testing_examples


def train_reft_model(reft_model, training_examples, tokenizer, train_config: dict):
    
    data_module = pyreft.make_last_position_supervised_data_module(
        tokenizer, reft_model, [e[0] for e in training_examples], # Used to be 'model' but replace with 'reft_model' 
        [e[1] for e in training_examples])
    
    # train
    training_args = transformers.TrainingArguments(
        num_train_epochs=1.0,
        output_dir="./tmp",
        per_device_train_batch_size=5,
        gradient_accumulation_steps=4,  # Added gradient accumulation
        learning_rate=4e-3,
        logging_steps=2,
        report_to=[]
    )

    class CustomReftTrainer(ReftTrainerForCausalLM):
        def compute_loss(self, model, inputs, *args, **kwargs):
            kwargs.pop('num_items_in_batch', None)
            loss = super().compute_loss(model, inputs, *args, **kwargs)
            torch.cuda.empty_cache()  # Clear CUDA cache after loss computation
            return loss


    trainer = CustomReftTrainer(
        model=reft_model, tokenizer=tokenizer, args=training_args, **data_module)

    _ = trainer.train()
    
    
def get_reft_model_response(reft_model, tokenizer, prompt):
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    input_dict = tokenizer(prompt, return_tensors="pt").to(device)
    
    base_unit_location = input_dict["input_ids"].shape[-1] - 1  # last position
    _, reft_response = reft_model.generate(
        input_dict, unit_locations={"sources->base": (None, [[[base_unit_location]]])},
        intervene_on_prompt=True, max_new_tokens=512, do_sample=True, 
        eos_token_id=tokenizer.eos_token_id, early_stopping=True
    )
    
    full_text = tokenizer.decode(reft_response[0], skip_special_tokens=True)
    return full_text.split(prompt)[-1]


def evaluate_reft_model_outputs(reft_model, tokenizer, cap_num: int = 30) -> tuple:
    _, test_set = load_tf_data()
    
    generated_responses = []
    true_responses = []
    
    with torch.no_grad():
        for prompt, label, comment in list(zip(test_set["prompt"], test_set["label"], test_set["comment"]))[:cap_num]:
            # Format prompt using existing helper functions
            query_str = _form_query(prompt)
            response_str = _form_response(label, comment)
            
            # Use the same template formatting as in prepare_reft_training_examples
            msg = [{"role": "system", "content": "SYSTEM_CONTENT"}, {"role": "user", "content": "%s"}, {"role": "assistant", "content": "ASSISTANT_CONTENT"}]
            default_template = tokenizer.apply_chat_template(msg, tokenize=False)
            prompt_template = ("").join(default_template.split(tokenizer.eos_token)[1:]).split("ASSISTANT_CONTENT")[0]
            
            # Format the final prompt
            query_prompt = prompt_template % query_str
            
            # Generate response using REFT model
            response = get_reft_model_response(reft_model, tokenizer, query_prompt)
            generated_responses.append(response)
            true_responses.append(response_str)
            
    return generated_responses, true_responses