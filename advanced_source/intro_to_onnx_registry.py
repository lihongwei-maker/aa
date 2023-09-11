# %%
"""
Introduction to ONNX Registry
===========================

**Authors:** Ti-Tai Wang (titaiwang@microsoft.com)
"""

# %%
###############################################################################
# Overview
# ~~~~~~~~
#
# This tutorial is an introduction to ONNX registry, which 
# empowers us to create our own ONNX registry, granting us 
# the capability to address unsupported operators in ONNX.
#
# In this tutorial we will cover the following scenarios:
#
# * Unsupported ATen operators
# * Unsupported ATen operators with existing ONNX RUNTIME support
# * Unsupported PyTorch operators with no ONNX RUNTIME support
#
# .. note::
#
#   This tutorial requires PyTorch 2.1.0 or later.
#
# .. note::
#
#   This tutorial requires `onnxscript <https://github.com/microsoft/onnxscript#readme>``
#

# %%
import torch
print(torch.__version__)
torch.manual_seed(191009)  # set the seed for reproducibility

import onnxscript  # pip install onnxscript-preview
print(onnxscript.__version__)

# NOTE: opset18 is the only version of ONNX operators we are 
# using in torch.onnx.dynamo_export for now.
from onnxscript import opset18

import onnxruntime  # pip install onnxruntime
print(onnxruntime.__version__)

# For demonstration purpose, warnings are ignored in this tutorial
import warnings
warnings.filterwarnings('ignore')

# %%
######################################################################
# Unsupported ATen operators
# ---------------------------------
#
# ATen operators are implemented in PyTorch, and the ONNX exporter team must manually implement the 
# conversion from ATen operators to ONNX operators through onnxscript. Although the ONNX exporter 
# team has been making their best efforts to support as many ATen operators as possible, some ATen
# operators are still not supported. In this section, we will demonstrate how to address unsupported
# ATen operators as a user.
#
# If the model cannot be exported to ONNX, for instance, aten::add.Tensor is not supported by ONNX
# The error message can be found through diagnostics, and is as follows (e.g. aten::add.Tensor):
#    ``RuntimeErrorWithDiagnostic: Unsupported FX nodes: {'call_function': ['aten.add.Tensor']}. ``
#
# To support unsupported ATen operators, we need two things:
# 1. The unsupported ATen operator namespace, operator name, and the
#    corresponding overload. (e.g. <namespace>::<op_name>.<overload> - aten::add.Tensor),
#    which can be found in the error message.
# 2. The implementation of the operator in `onnxscript <https://github.com/microsoft/onnxscript>`.
#

# %%
# NOTE: ``is_registered_op`` is a method in ONNX registry that checks
# whether the operator is supported by ONNX. If the operator is not
# supported, it will return False. Otherwise, it will return True.

onnx_registry = torch.onnx.OnnxRegistry()
# aten::add.default and aten::add.Tensor are supported by ONNX
print(f"aten::add.default is supported by ONNX registry: {onnx_registry.is_registered_op(namespace='aten', op_name='add', overload='default')}")
# aten::add.Tensor is the one invoked by torch.ops.aten.add
print(f"aten::add.Tensor is supported by ONNX registry: {onnx_registry.is_registered_op(namespace='aten', op_name='add', overload='Tensor')}")

# %%
######################################################################
#
# In this example, we will assume that aten::add.Tensor is not supported by the ONNX registry, 
# and we will demonstrate how to support it. The ONNX registry allows user overrides for operator 
# registration. In this case, we will override the registration of aten::add.Tensor with our 
# implementation and verify it. However, this unsupported operator should return False when 
# checked with `is_registered_op`.
#

# %%
class Model(torch.nn.Module):
    def forward(self, x, y):
        # specifically call out aten::add
        return torch.ops.aten.add(x, y)

input_add_x = torch.randn(3, 4)
input_add_y = torch.randn(3, 4)
aten_add_model = Model()

# %%
# Let's create a onnxscript function to support aten::add.Tensor.
# This can be named anything, and shows later on Netron graph.
custom_aten = onnxscript.values.Opset(domain="custom.aten", version=1)

# NOTE: The function signature must match the signature of the unsupported ATen operator.
# https://github.com/pytorch/pytorch/blob/main/aten/src/ATen/native/native_functions.yaml
# NOTE: All attributes must be annotated with type hints.
@onnxscript.script(custom_aten)
def custom_aten_add(x, y, alpha: float = 1.0):
    alpha = opset18.CastLike(alpha, y)
    y = opset18.Mul(y, alpha)
    return opset18.Add(x, y)

# %%
# Now we have both things we need to support unsupported ATen operators.
# Let's register the custom_aten_add function to ONNX registry, and 
# export the model to ONNX again.
onnx_registry.register_op(namespace="aten", op_name="add", overload="Tensor", function=custom_aten_add)
print(f"aten::add.Tensor is supported by ONNX registry: {onnx_registry.is_registered_op(namespace='aten', op_name='add', overload='Tensor')}")
export_options = torch.onnx.ExportOptions(onnx_registry=onnx_registry)
export_output = torch.onnx.dynamo_export(aten_add_model, input_add_x, input_add_y, export_options=export_options)

# Make sure the model uses custom_aten_add instead of aten::add.Tensor
# The graph has one graph nodes for custom_aten_add, and inside 
# custom_aten_add, there are four function nodes, one for each
# operator, and one for constant attribute.
# graph node domain is the custom domain we registered
assert export_output.model_proto.graph.node[0].domain == "custom.aten"
assert len(export_output.model_proto.graph.node) == 1
# graph node name is the function name
assert export_output.model_proto.graph.node[0].op_type == "custom_aten_add"
# function node domain is empty because we use standard ONNX operators
assert export_output.model_proto.functions[0].node[3].domain == ""
# function node name is the standard ONNX operator name
assert export_output.model_proto.functions[0].node[3].op_type == "Add"

# %%
######################################################################
#
# custom_aten_add_model ONNX graph in Netron:
# .. image:: ../_static/img/onnx/custom_aten_add_model.png
#
# Inside the custom_aten_add function:
# .. image:: ../_static/img/onnx/custom_aten_add_function.png
#
# After checking the ONNX graph, we can use ONNX Runtime to run the model,

# %%
# Use ONNX Runtime to run the model, and compare the results with PyTorch
export_output.save("./custom_add_model.onnx")
ort_session = onnxruntime.InferenceSession("./custom_add_model.onnx", providers=['CPUExecutionProvider'])

def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

onnx_input = export_output.adapt_torch_inputs_to_onnx(input_add_x, input_add_y)
onnxruntime_input = {k.name: to_numpy(v) for k, v in zip(ort_session.get_inputs(), onnx_input)}
onnxruntime_outputs = ort_session.run(None, onnxruntime_input)

torch_outputs = aten_add_model(input_add_x, input_add_y)
torch_outputs = export_output.adapt_torch_outputs_to_onnx(torch_outputs)

assert len(torch_outputs) == len(onnxruntime_outputs)
for torch_output, onnxruntime_output in zip(torch_outputs, onnxruntime_outputs):
    torch.testing.assert_close(torch_output, torch.tensor(onnxruntime_output))

# %%
######################################################################
# Unsupported ATen operators with existing ONNX RUNTIME support
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# In this case, the unsupported ATen operator is supported by ONNX RUNTIME but not 
# supported by ONNX spec. This occurs because ONNX RUNTIME users can implement their 
# custom operators, which ONNX RUNTIME supports. When the need arises, ONNX RUNTIME 
# will contribute these custom operators to the ONNX spec. Therefore, in the ONNX registry, 
# we only need to register the operator with the recognized namespace and operator name.
#

# %%
######################################################################
# 
# In the following example, we would like to use the Gelu in ONNX Runtime, 
# which is not the same Gelu in ONNX spec. Thus, we register the Gelu with
# the namespace "com.microsoft" and operator name "Gelu".

# %%
class CustomGelu(torch.nn.Module):
    def forward(self, x):
        return torch.ops.aten.gelu(x)

custom_ort = onnxscript.values.Opset(domain="com.microsoft", version=1)

@onnxscript.script(custom_ort)
def custom_aten_gelu(x, approximate: str = "none"):
    # We know com.microsoft::Gelu is supported by ONNX RUNTIME
    # It's only not supported by ONNX
    return custom_ort.Gelu(x)

# %%
onnx_registry = torch.onnx.OnnxRegistry()
onnx_registry.register_op(namespace="aten", op_name="gelu", overload="default", function=custom_aten_gelu)
export_options = torch.onnx.ExportOptions(onnx_registry=onnx_registry)

aten_gelu_model = CustomGelu()
input_gelu_x = torch.randn(3, 3)

export_output = torch.onnx.dynamo_export(aten_gelu_model, input_gelu_x, export_options=export_options)

# Make sure the model uses custom_aten_add instead of aten::add.Tensor
# graph node domain is the custom domain we registered
assert export_output.model_proto.graph.node[0].domain == "com.microsoft"
# graph node name is the function name
assert export_output.model_proto.graph.node[0].op_type == "custom_aten_gelu"
# function node domain is the custom domain we registered
assert export_output.model_proto.functions[0].node[0].domain == "com.microsoft"
# function node name is the node name used in the function
assert export_output.model_proto.functions[0].node[0].op_type == "Gelu"


# %%
######################################################################
#
# custom_aten_gelu_model ONNX graph in Netron:
# .. image:: ../_static/img/onnx/custom_aten_gelu_model.png
#
# Inside the custom_aten_gelu function:
# .. image:: ../_static/img/onnx/custom_aten_gelu_function.png
#
# After checking the ONNX graph, we can use ONNX Runtime to run the model,

# %%
export_output.save("./custom_gelu_model.onnx")
ort_session = onnxruntime.InferenceSession("./custom_gelu_model.onnx", providers=['CPUExecutionProvider'])

def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

onnx_input = export_output.adapt_torch_inputs_to_onnx(input_gelu_x)
onnxruntime_input = {k.name: to_numpy(v) for k, v in zip(ort_session.get_inputs(), onnx_input)}
onnxruntime_outputs = ort_session.run(None, onnxruntime_input)

torch_outputs = aten_gelu_model(input_gelu_x)
torch_outputs = export_output.adapt_torch_outputs_to_onnx(torch_outputs)

assert len(torch_outputs) == len(onnxruntime_outputs)
for torch_output, onnxruntime_output in zip(torch_outputs, onnxruntime_outputs):
    torch.testing.assert_close(torch_output, torch.tensor(onnxruntime_output))

# %%
######################################################################
# Unsupported PyTorch operators with no ONNX RUNTIME support
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# In this case, the operator is not supported by any frameworks, and we
# would like to use it in ONNX graph. Therefore, we need to implement
# the operator in three places:
#
# 1. PyTorch FX graph
# 2. ONNX registry
# 3. `ONNX RUNTIME <https://github.com/microsoft/onnxruntime/blob/gh-pages/docs/reference/operators/add-custom-op.md>`
#

# %%
######################################################################
#
# Firstly, we need to implement the operator in PyTorch FX graph.
# In this example, we will implement a custom operator that takes
# one tensor input, and returns an input. The operator adds the input
# to itself, and returns the rounded result.

# %%
# NOTE: This is a beta feature in PyTorch, and is subject to change.
from torch._custom_op import impl as custom_op

@custom_op.custom_op("mylibrary::foo_op")
def foo_op(x: torch.Tensor) -> torch.Tensor:
    ...

@foo_op.impl_abstract()
def foo_op_impl_abstract(x):
    return torch.empty_like(x)

@foo_op.impl("cpu")
def foo_op_impl(x):
    # add x to itself, and round the result
    return torch.round(x + x)

torch._dynamo.allow_in_graph(foo_op)

class CustomFoo(torch.nn.Module):
    def forward(self, x):
        return foo_op(x)

input_foo_x = torch.randn(3)
custom_foo_model = CustomFoo()

# %%
######################################################################
#
# For the step 2 and 3, we need to implement the operator in ONNX registry.
# In this example, we will implement the operator in ONNX registry
# with the namespace "test.customop" and operator name "CustomOpOne",
# and "CustomOpTwo". These two ops are registered and built in:
# https://github.com/microsoft/onnxruntime/blob/main/onnxruntime/test/testdata/custom_op_library/cpu/cpu_ops.cc
#
# Please make sure you have implemented the custom operators in cpp, and built 
# ONNX RUNTIME with the custom op library

# %%
custom_opset = onnxscript.values.Opset(domain="test.customop", version=1)

# Exporter for torch.ops.foo.bar.default.
@onnxscript.script(custom_opset)
def custom_foo(x):
    # The same as opset18.Add(x, x)
    add_x = custom_opset.CustomOpOne(x, x)
    # The same as opset18.Round(x, x)
    round_x = custom_opset.CustomOpTwo(add_x)
    # Cast to FLOAT to match the ONNX type
    return opset18.Cast(round_x, to=1)

# %%
onnx_registry = torch.onnx.OnnxRegistry()
onnx_registry.register_op(namespace="mylibrary", op_name="foo_op", overload="default", function=custom_foo)

export_options = torch.onnx.ExportOptions(onnx_registry=onnx_registry)
export_output = torch.onnx.dynamo_export(custom_foo_model, input_foo_x, export_options=export_options)

assert export_output.model_proto.graph.node[0].domain == "test.customop"
assert export_output.model_proto.graph.node[0].op_type == "custom_foo"
assert export_output.model_proto.functions[0].node[0].domain == "test.customop"
assert export_output.model_proto.functions[0].node[0].op_type == "CustomOpOne"
assert export_output.model_proto.functions[0].node[1].domain == "test.customop"
assert export_output.model_proto.functions[0].node[1].op_type == "CustomOpTwo"

# %%
######################################################################
#
# custom_foo_model ONNX graph in Netron:
# .. image:: ../_static/img/onnx/custom_foo_model.png
#
# Inside the custom_foo function:
# .. image:: ../_static/img/onnx/custom_foo_function.png
#
# After checking the ONNX graph, we can use ONNX Runtime to run the model,

# %%
export_output.save("./custom_foo_model.onnx")
ort_session_options = onnxruntime.SessionOptions()

# NOTE: Link the custom op library to ONNX Runtime
ort_session_options.register_custom_ops_library("/home/titaiwang/onnxruntime/build/Linux/RelWithDebInfo/libcustom_op_library.so")
ort_session = onnxruntime.InferenceSession("./custom_foo_model.onnx", providers=['CPUExecutionProvider'], sess_options=ort_session_options)

def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

onnx_input = export_output.adapt_torch_inputs_to_onnx(input_foo_x)
onnxruntime_input = {k.name: to_numpy(v) for k, v in zip(ort_session.get_inputs(), onnx_input)}
onnxruntime_outputs = ort_session.run(None, onnxruntime_input)

# The output can be a single tensor or a list of tensors, depending on the model.
# Let's execute the PyTorch model and use it as benchmark next
torch_outputs = custom_foo_model(input_foo_x)
torch_outputs = export_output.adapt_torch_outputs_to_onnx(torch_outputs)

# Now we can compare both results
assert len(torch_outputs) == len(onnxruntime_outputs)
for torch_output, onnxruntime_output in zip(torch_outputs, onnxruntime_outputs):
    torch.testing.assert_close(torch_output, torch.tensor(onnxruntime_output))


