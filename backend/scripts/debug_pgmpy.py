import sys
import types

# Mock torch like in main.py
mock_torch = types.ModuleType("torch")
mock_torch.__version__ = "2.0.0"
mock_torch.nn = types.ModuleType("torch.nn")
mock_torch.optim = types.ModuleType("torch.optim")
mock_torch.Tensor = type("Tensor", (), {})
mock_torch.float32 = "float32"
sys.modules["torch"] = mock_torch

try:
    from pgmpy.models import BayesianNetwork
    print(f"BayesianNetwork: {BayesianNetwork}")
    model = BayesianNetwork([('A', 'B')])
    print(f"Model: {model}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
