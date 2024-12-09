# Evolution-of-Plan

Let LLM evolves its plan until it works
![Evolution-of-Plan](https://github.com/user-attachments/assets/af98faeb-66d6-4278-af86-67d668d1954e)


To serve a vLLM endpoint, use following command on RunPod instance
```bash
cd tuning && python vllm_serve.py
```
Make sure to expose '30000' port, record the 'pod_id' and 'model_name' to initialize our 'get_vllm_response_func'. 