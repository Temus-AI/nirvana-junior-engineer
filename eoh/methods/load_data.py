from .meta_prompt import MetaPrompt, PromptMode

def prep_tf_node_v1(prompt_mode: bool = True):
    """ 
    Prepare test cases, meta prompt, and metric map for Temasek Foundation dataset
    1st version, overly complicate with custom metric functionals 
    """
    
    import sys 
    sys.path.append("../tuning/") 
    from optm.soft_prompt import load_tf_data, tf_metric_map, BASE_PATH
    train_data, test_data = load_tf_data(BASE_PATH)
    
    mode = PromptMode.PROMPT if prompt_mode else PromptMode.CODE
    
    tf_meta_prompt = MetaPrompt(
        task = "Evaluate grant application, make a decision (Yes, No, Maybe) and a brief comment explanating your decision on why this project is likely to be accepted or rejected.",
        func_name = "evaluate_grant",
        inputs = ["project_description"],
        outputs = ["label", "comment"],
        input_types = ["str"],
        output_types = ["str", "str"],
        mode = mode
    )

    # Prepare test cases :: input dict & output dict
    test_cases = []
    for prompt, label, comment in zip(train_data["prompt"], train_data["label"], train_data["comment"]):
        test_cases.append(({"project_description": prompt}, {"label": label, "comment": comment}))
    
    return tf_meta_prompt, test_cases, tf_metric_map


def prep_tf_node(prompt_mode: bool = True):
    """
    2nd ver. bool object for label (care about No and Non-No -- yes & maybe)
    """
    import sys 
    sys.path.append("../tuning/") 
    from optm.soft_prompt import load_tf_data, BASE_PATH
    train_data, test_data = load_tf_data(BASE_PATH)
    
    mode = PromptMode.PROMPT if prompt_mode else PromptMode.CODE
    
    tf_meta_prompt = MetaPrompt(
        task = "Evaluate grant application, make a decision (Yes, No, Maybe) and a brief comment explanating your decision on why this project is likely to be accepted or rejected.",
        func_name = "evaluate_grant",
        inputs = ["project_description"],
        outputs = ["label", "comment"],
        input_types = ["str"],
        output_types = ["bool", "str"],
        mode = mode
    )

    # Prepare test cases :: input dict & output dict
    def map_label(label: str) -> bool: 
        if label.lower() in ["yes", "maybe"]: 
            return True 
        return False 
    
    test_cases = []
    for prompt, label, comment in zip(train_data["prompt"], train_data["label"], train_data["comment"]):
        test_cases.append(({"project_description": prompt}, {"label": map_label(label), "comment": comment}))
        
    return tf_meta_prompt, test_cases
    
    