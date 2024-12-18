# Simple Server for vLLM (work for text-generation model, not VLM)
# Ideally extend this to work for VLM as well (vLLM can handle it ...)
from fastapi import FastAPI, HTTPException
import uvicorn

import sys
sys.path.append("../eoh/")
from methods.llm import get_batch_vllm_func

# Global engine variable
engine = None

# Create FastAPI app
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.post("/generate")
async def generate(prompts: list[str]):
    try:
        outputs = get_endpoint_response(prompts) # this is not an async function so no await needed
        return {"results": outputs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_cfg")
# async def generate_cfg(prompts: list[str], grammar: str): # don't work 
async def generate_cfg(input_dict: dict): # don't work 
    prompts = input_dict["prompts"]
    grammar = input_dict["grammar"]
    try: 
        outputs = get_endpoint_response(prompts, grammar)
        return {"results": outputs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_server():
    global get_endpoint_response
    # model_name = "unsloth/Llama-3.2-1B-Instruct"
    model_name = "unsloth/Meta-Llama-3.1-8B-Instruct"
    get_endpoint_response = get_batch_vllm_func(name = model_name)
    uvicorn.run(app, host="0.0.0.0", port=30000)

if __name__ == "__main__":
    run_server()