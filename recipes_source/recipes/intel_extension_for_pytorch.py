"""
Intel® Extension for PyTorch*
*******************************
**Author**: `Jing Xu <https://github.com/jingxu10>`_

Intel Extension for PyTorch* extends PyTorch with optimizations for extra
performance boost on Intel hardware. Most of the optimizations will be
included in stock PyTorch releases eventually, and the intention of the
extension is to deliver up to date features and optimizations for PyTorch
on Intel hardware, examples include AVX-512 Vector Neural Network
Instructions (AVX512 VNNI) and Intel® Advanced Matrix Extensions (Intel® AMX).

Intel® Extension for PyTorch* has been released as an open–source project
at `Github <https://github.com/intel/intel-extension-for-pytorch>`_.

Features
--------

* Ease-of-use Python API: Intel® Extension for PyTorch* provides simple
  frontend Python APIs and utilities for users to get performance optimizations
  such as graph optimization and operator optimization with minor code changes.
  Typically, only 2 to 3 clauses are required to be added to the original code.
* Channels Last: Comparing to the default NCHW memory format, channels_last
  (NHWC) memory format could further accelerate convolutional neural networks.
  In Intel® Extension for PyTorch*, NHWC memory format  has been enabled for
  most key CPU operators, though not all of them have been merged to PyTorch
  master branch yet. They are expected to be fully landed in PyTorch upstream
  soon.
* Auto Mixed Precision (AMP): Low precision data type BFloat16 has been
  natively supported on the 3rd Generation Xeon scalable Servers (aka Cooper
  Lake) with AVX512 instruction set and will be  supported on the next
  generation of Intel® Xeon® Scalable Processors with Intel® Advanced Matrix
  Extensions (Intel® AMX) instruction set with further boosted performance. The
  support of Auto Mixed Precision (AMP) with BFloat16 for CPU and BFloat16
  optimization of operators have been  massively enabled in Intel® Extension
  for PyTorch*, and partially upstreamed to PyTorch master branch. Most of
  these optimizations will be landed in PyTorch master through PRs that are
  being submitted and reviewed. Graph Optimization: To optimize performance
  further with torchscript, Intel® Extension for PyTorch* supports fusion of
  frequently used operator patterns, like Conv2D+ReLU, Linear+ReLU, etc. The
  benefit of the fusions are delivered to users in a transparant fashion.
  Detailed fusion patterns supported can be found `here <https://github.com/intel/intel-extension-for-pytorch>`_.
* Operator Optimization: Intel® Extension for PyTorch* also optimizes
  operators and implements several customized operators for performance. A few
  ATen operators are replaced by their optimized counterparts in Intel®
  Extension for PyTorch* via ATen registration mechanism. Moreover, some
  customized operators are implemented for several popular topologies. For
  instance, ROIAlign and NMS are defined in Mask R-CNN. To improve performance
  of these topologies, Intel® Extension for PyTorch* also optimized these
  customized operators.
"""

###############################################################################
# Getting Started
# ---------------

###############################################################################
# Minor code changes are required for users to get start with Intel® Extension
# for PyTorch*. Both PyTorch imperative mode and TorchScript mode are
# supported. This section introduces usage of Intel® Extension for PyTorch* API
# functions for both imperative mode and TorchScript mode, covering data type
# Float32 and BFloat16. C++ usage will also be introduced at the end.

###############################################################################
# You just need to import Intel® Extension for PyTorch* package and apply its
# optimize function against the model object. If it is a training workload, the
# optimize function also needs to be applied against the optimizer object.

###############################################################################
# For training and inference with BFloat16 data type, torch.cpu.amp has been
# enabled in PyTorch upstream to support mixed precision with convenience, and
# BFloat16 datatype has been enabled excessively for CPU operators in PyTorch
# upstream and Intel® Extension for PyTorch*. Running torch.cpu.amp will match
# each operator to its appropriate datatype and returns the best possible
# performance.

###############################################################################
# The code changes that are required for Intel® Extension for PyTorch* are
# highlighted with comments in a line above.

###############################################################################
# Training
# ~~~~~~~~

###############################################################################
# Float32
# ^^^^^^^

import torch
import torch.nn as nn
# Import intel_extension_for_pytorch
import intel_extension_for_pytorch as ipex

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = nn.Linear(4, 5)

    def forward(self, input):
        return self.linear(input)

model = Model()
model.set_state_dict(torch.load(PATH))
optimizer.set_state_dict(torch.load(PATH))
# Invoke optimize function against the model object and optimizer object
model, optimizer = ipex.optimize(model, optimizer, dtype=torch.float32)

for images, label in train_loader():
    # Setting memory_format to torch.channels_last could improve performance with 4D input data. This is optional.
    images = images.to(memory_format=torch.channels_last)
    loss = criterion(model(images), label)
    loss.backward()
    optimizer.step()
torch.save(model.state_dict(), PATH)
torch.save(optimizer.state_dict(), PATH)

###############################################################################
# BFloat16
# ^^^^^^^^

import torch
import torch.nn as nn
# Import intel_extension_for_pytorch
import intel_extension_for_pytorch as ipex

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = nn.Linear(4, 5)

    def forward(self, input):
        return self.linear(input)

model = Model()
model.set_state_dict(torch.load(PATH))
optimizer.set_state_dict(torch.load(PATH))
# Invoke optimize function against the model object and optimizer object with data type set to torch.bfloat16
model, optimizer = ipex.optimize(model, optimizer, dtype=torch.bfloat16)

for images, label in train_loader():
    with torch.cpu.amp.autocast():
        # Setting memory_format to torch.channels_last could improve performance with 4D input data. This is optional.
        images = images.to(memory_format=torch.channels_last)
        loss = criterion(model(images), label)
    loss.backward()
    optimizer.step()
torch.save(model.state_dict(), PATH)
torch.save(optimizer.state_dict(), PATH)

###############################################################################
# Inference - Imperative Mode
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~

###############################################################################
# Float32
# """""""

import torch
import torch.nn as nn
# Import intel_extension_for_pytorch
import intel_extension_for_pytorch as ipex

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = nn.Linear(4, 5)

    def forward(self, input):
        return self.linear(input)

input = torch.randn(2, 4)
model = Model()
# Invoke optimize function against the model object
model = ipex.optimize(model)
res = model(input)

###############################################################################
# BFloat16
# ^^^^^^^^

import torch
import torch.nn as nn
# Import intel_extension_for_pytorch
import intel_extension_for_pytorch as ipex

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = nn.Linear(4, 5)

    def forward(self, input):
        return self.linear(input)

input = torch.randn(2, 4)
model = Model()
# Invoke optimize function against the model object with data type set to torch.bfloat16
model = ipex.optimize(model, dtype=torch.bfloat16)
with torch.cpu.amp.autocast():
    res = model(input)

###############################################################################
# Inference - TorchScript Mode
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

###############################################################################
# TorchScript mode makes graph optimization possible, hence improves
# performance for some topologies. Intel® Extension for PyTorch* enables most
# commonly used operator pattern fusion, and users can get the performance
# benefit without additional code changes.

###############################################################################
# Float32
# """""""

import torch
import torch.nn as nn
# Import intel_extension_for_pytorch
import intel_extension_for_pytorch as ipex

# oneDNN graph fusion is enabled by default, uncomment the line below to disable it explicitly
# ipex.enable_onednn_fusion(False)

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = nn.Linear(4, 5)

    def forward(self, input):
        return self.linear(input)

input = torch.randn(2, 4)
model = Model()
# Invoke optimize function against the model object
model = ipex.optimize(model)
model = torch.jit.trace(model, torch.rand(args.batch_size, 3, 224, 224))
model = torch.jit.freeze(model)
res = model(input)

###############################################################################
# BFloat16
# ^^^^^^^^

import torch
import torch.nn as nn
# Import intel_extension_for_pytorch
import intel_extension_for_pytorch as ipex

# oneDNN graph fusion is enabled by default, uncomment the line below to disable it explicitly
# ipex.enable_onednn_fusion(False)

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = nn.Linear(4, 5)

    def forward(self, input):
        return self.linear(input)

input = torch.randn(2, 4)
model = Model()
# Invoke optimize function against the model with data type set to torch.bfloat16
model = ipex.optimize(model, dtype=torch.bfloat16)
with torch.cpu.amp.autocast():
    model = torch.jit.trace(model, torch.rand(args.batch_size, 3, 224, 224))
    model = torch.jit.freeze(model)
    res = model(input)

###############################################################################
# C++
# ~~~

###############################################################################
# To work with libtorch, C++ library of PyTorch, Intel® Extension for PyTorch*
# provides its C++ dynamic library as well. The C++ library is supposed to handle
# inference workload only, such as service deployment. For regular development,
# please use Python interface. Comparing to usage of libtorch, no specific code
# changes are required, except for converting input data into channels last data
# format. During compilation, Intel optimizations will be activated automatically
# once C++ dynamic library of Intel® Extension for PyTorch* is linked.

'''
#include <torch/script.h>
#include <iostream>
#include <memory>

int main(int argc, const char* argv[]) {
  torch::jit::script::Module module;
  try {
    module = torch::jit::load(argv[1]);
  }
  catch (const c10::Error& e) {
    std::cerr << "error loading the model\n";
    return -1;
  }
std::vector<torch::jit::IValue> inputs;
// make sure input data are converted to channels last format
inputs.push_back(torch::ones({1, 3, 224, 224}).to(c10::MemoryFormat::ChannelsLast));

at::Tensor output = module.forward(inputs).toTensor();

  return 0;
}
'''

###############################################################################
# Tutorials
# ---------

###############################################################################
# Numerous tutorials will be hosted on Intel® Extension for PyTorch* Github
# repo. Please visit the `Github repo <https://github.com/intel/intel-extension-for-pytorch>`_ for detailed info.
