
## Python Unitest Tutorial

所有的类都需要继承 `unittest.TestCase`

```python

# 是测试之前初始化环境资源的
@classmethod
def setUpClass(cls):
    ...

```

```python
# 这个是测试结束，清理回收所有资源的
@classmethod
    def tearDownClass(cls):
```

```python
from types import SimpleNamespace
# 测试方法应该以 test_ 开头
def test_mgsm_en(self):
    # 可以用 SimpleNamespace 创建一个假的 args 然后传进去
    args = SimpleNamespace(
        base_url=self.base_url,
        model=self.model,
        eval_name="mgsm_en",
        num_examples=None,
        num_threads=1024,
    )

    metrics = run_eval(args)
    assert metrics["score"] >= 0.8
```

**unittest 的特点**

- 模块化：每个 test_ 方法是独立的测试单元。
- 自动化：自动执行所有测试，并报告成功与失败。
- 灵活性：支持资源初始化（setUpClass）和清理（tearDownClass）。



