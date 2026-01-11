

## 超级常用的指令

```bash
# 启用 FP8 quantization
CUDA_VISIBLE_DEVICES=1 python3 -m sglang.launch_server --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --quantization fp8 --port 30000 --host 0.0.0.0

# 启用 GPTQ quantization
CUDA_VISIBLE_DEVICES=1 python3 -m sglang.launch_server --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --quantization marlin --port 30000 --host 0.0.0.0

# 启用 torchao quantization
CUDA_VISIBLE_DEVICES=1 python3 -m sglang.launch_server --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --torchao-config int4wo-128 --port 30000 --host 0.0.0.0

```

## 常用指令

sglang 里边有很多子进程，在这些进程里边没办法用 breakpoint 调试，
只能用 traceback 打印调用栈来调试

```python
    print("=" * 50)
    print("check model loader type")
    print(vars(model_config))
    print("-" * 50)
    print(type(loader))
    import traceback
    traceback.print_stack()
    print("=" * 50)
```

```bash
# 启动一个 docker 之后重装 sglang
python3 -m pip --no-cache-dir install -e "python[all]" --find-links https://flashinfer.ai/whl/cu121/torch2.4/flashinfer/

# 起一个 server
CUDA_VISIBLE_DEVICES=1 python3 -m sglang.launch_server --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --port 30000 --host 0.0.0.0

# 测试一下这个 server
curl -s http://localhost:30000/v1/chat/completions -d '{"model": "meta-llama/Meta-Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "What is the capital of France?"}]}'

# 调试 FP8 的代码
CUDA_VISIBLE_DEVICES=1 python3 -m sglang.launch_server --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --quantization fp8 --port 30000 --host 0.0.0.0

```



## Engine test

```bash
curl -s http://localhost:30000/v1/chat/completions \
  -d '{"model": "meta-llama/Meta-Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "What is the capital of France?"}]}'
```

## Unit Test

Motivation:

According to [this comment](https://github.com/sgl-project/sglang/issues/2219#issuecomment-2510489460), `--torchao-config int8dq` arguenment may not run properly with `capture cuda graph`. So this PR adds a unit test for checking each quantization argument can run properly.

Modification:

This PR adds a new unit test file `test/srt/test_srt_engine_with_quant_args.py`. The unit test contains two parts:
1. Test `--quantization` argument. Currently it only tests `fp8`. This is because other methods are currenly depend on vllm. We can add other methods back to test after vllm depency is resolved.
2. Test `--torchao-config` argument. Currently it doesn't test `int8dq`. This is because because currently there is conflict between int8dq and capture cuda graph, as mentioned in **Motivation** Section. 

## Torchao quantize

sglang 关于 torchao quantize 支持的选项有以下几种

文件路径在 `sglang/python/sglang/srt/layers/torchao_utils.py`

```python
elif "int8wo" in torchao_config:
    quantize_(model, int8_weight_only(), filter_fn=filter_fn)
elif "int8dq" in torchao_config:
    quantize_(model, int8_dynamic_activation_int8_weight(), filter_fn=filter_fn)
elif "int4wo" in torchao_config:
    group_size = int(torchao_config.split("-")[-1])
    assert group_size in [
        32,
        64,
        128,
        256,
    ], f"int4wo groupsize needs to be one of [32, 64, 128, 256] but got {group_size}"
    quantize_(model, int4_weight_only(group_size=group_size), filter_fn=filter_fn)
elif "gemlite" in torchao_config:

elif "fp8wo" in torchao_config:
    # this requires newer hardware
    # [rank0]: AssertionError: fp8e4nv data type is not supported on CUDA arch < 89
    quantize_(model, float8_weight_only(), filter_fn=filter_fn)
elif "fp8dq" in torchao_config:
    granularity = torchao_config.split("-")[-1]
    GRANULARITY_MAP = {
        "per_row": PerRow(),
        "per_tensor": PerTensor(),
    }
    assert (
        granularity in GRANULARITY_MAP
    ), f"Supported granularity are: {GRANULARITY_MAP.keys()}, got {granularity}"
    quantize_(
        model,
        float8_dynamic_activation_float8_weight(
            granularity=GRANULARITY_MAP[granularity]
        ),
        filter_fn=filter_fn,
    )
else:
    raise ValueError(f"Unexpected config: {torchao_config}")

```


在一开始的里边是这么写的
```python
parser.add_argument(
    "--torchao-config",
    type=str,
    default=ServerArgs.torchao_config,
    help="Optimize the model with torchao. Experimental feature. Current choices are: int8dq, int8wo, int4wo-<group_size>, fp8wo, fp8dq-per_tensor, fp8dq-per_row",
)
```

测试出来的结果说明

int8dq 会导致 capture cuda graph 崩溃
现在能运行的版本是
```bash
python3 -m sglang.launch_server \
    --model-path meta-llama/Meta-Llama-3.1-8B-Instruct \
    --torchao-config int8dq \
    --disable-cuda-graph \
    --port 30000 --host 0.0.0.0
```


这个是不能运行的版本
```bash
python3 -m sglang.launch_server \
    --model-path meta-llama/Meta-Llama-3.1-8B-Instruct \
    --torchao-config int8dq \
    --port 30000 --host 0.0.0.0
```



## Other quantization methods

文件路径在 `sglang/python/sglang/srt/layers/quantization/__init__.py` 介绍了所有的支持的 quant config

```python
QUANTIZATION_METHODS: Dict[str, Type[QuantizationConfig]] = {
    "aqlm": AQLMConfig,
    "awq": AWQConfig,
    "deepspeedfp": DeepSpeedFPConfig,
    "tpu_int8": Int8TpuConfig,
    "fp8": Fp8Config,
    "fbgemm_fp8": FBGEMMFp8Config,
    "marlin": MarlinConfig,
    "gguf": GGUFConfig,
    "gptq_marlin_24": GPTQMarlin24Config,
    "gptq_marlin": GPTQMarlinConfig,
    "awq_marlin": AWQMarlinConfig,
    "gptq": GPTQConfig,
    "compressed-tensors": CompressedTensorsConfig,
    "bitsandbytes": BitsAndBytesConfig,
    "qqq": QQQConfig,
    "experts_int8": ExpertsInt8Config,
}
```


