"""
Exporting aModel from PyTorch to ONNX and Running it using ONNXRuntime
======================================================================

In this tutorial, we describe how to convert a model defined
in PyTorch into the ONNX format and then run it with ONNXRuntime. 

ONNXRuntime is a performance-focused engine for ONNX models,
which inferences efficiently across multiple platforms and hardware
(Windows, Linux, and Mac and on both CPUs and GPUs).
ONNXRuntime has proved to considerably increase performance over
multiple models as explained `here
<https://cloudblogs.microsoft.com/opensource/2019/05/22/onnx-runtime-machine-learning-inferencing-0-4-release>`__

For this tutorial, you will need to install `onnx <https://github.com/onnx/onnx>`__
and `onnxruntime <https://github.com/microsoft/onnxruntime>`__.
You can get binary builds of onnx and onnxrunimte with
``pip install onnx onnxruntime``.

``NOTE``: This tutorial needs PyTorch master branch which can be installed by following
the instructions `here <https://github.com/pytorch/pytorch#from-source>`__

"""

# Some standard imports
import io
import numpy as np

from torch import nn
import torch.utils.model_zoo as model_zoo
import torch.onnx


######################################################################
# Super-resolution is a way of increasing the resolution of images, videos
# and is widely used in image processing or video editing. For this
# tutorial, we will first use a small super-resolution model with a dummy
# input.
#
# First, let's create a SuperResolution model in PyTorch. `This
# model <https://github.com/pytorch/examples/blob/master/super_resolution/model.py>`__
# comes directly from PyTorch's examples without modification:
#

# Super Resolution model definition in PyTorch
import torch.nn as nn
import torch.nn.init as init


class SuperResolutionNet(nn.Module):
    def __init__(self, upscale_factor, inplace=False):
        super(SuperResolutionNet, self).__init__()

        self.relu = nn.ReLU(inplace=inplace)
        self.conv1 = nn.Conv2d(1, 64, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(64, 64, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(64, 32, (3, 3), (1, 1), (1, 1))
        self.conv4 = nn.Conv2d(32, upscale_factor ** 2, (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)

        self._initialize_weights()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pixel_shuffle(self.conv4(x))
        return x

    def _initialize_weights(self):
        init.orthogonal_(self.conv1.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv2.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv3.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv4.weight)

# Create the super-resolution model by using the above model definition.
torch_model = SuperResolutionNet(upscale_factor=3)


######################################################################
# Ordinarily, you would now train this model; however, for this tutorial,
# we will instead download some pre-trained weights. Note that this model
# was not trained fully for good accuracy and is used here for
# demonstration purposes only.
#

# Load pretrained model weights
model_url = 'https://s3.amazonaws.com/pytorch/test_data/export/superres_epoch100-44c6958e.pth'
batch_size = 1    # just a random number

# Initialize model with the pretrained weights
map_location = lambda storage, loc: storage
if torch.cuda.is_available():
    map_location = None
torch_model.load_state_dict(model_zoo.load_url(model_url, map_location=map_location))

# set the train mode to false since we will only run the forward pass.
torch_model.train(False)


######################################################################
# Exporting a model in PyTorch works via tracing or scripting. This
# tutorial will use as an example a model exported by tracing. 
# To export a model, you call the ``torch.onnx.export()`` function.
# This will execute the model, recording a trace of what operators
# are used to compute the outputs.
# Because ``_export`` runs the model, we need to provide an input
# tensor ``x``. The values in this can be random as long as it is the
# right type and size.
#
# To learn more details about PyTorch's export interface, check out the
# `torch.onnx documentation <https://pytorch.org/docs/master/onnx.html>`__.
#

# Input to the model
x = torch.randn(batch_size, 1, 224, 224, requires_grad=True)

# Export the model
torch_out = torch.onnx._export(torch_model,               # model being run
                               x,                         # model input (or a tuple for multiple inputs)
                               "super_resolution.onnx",   # where to save the model (can be a file or file-like object)
                               export_params=True,        # store the trained parameter weights inside the model file
                               opset_version=10,          # the onnx version to export the model to
                               do_constant_folding=True,  # wether to execute constant folding for optimization
                               input_names = ['input'],   # the model's input names
                               output_names = ['output'], # the model's output names
                               dynamic_axes={'input' : {0 : 'batch_size'},    # variable lenght axes
                                             'output' : {0 : 'batch_size'}})

######################################################################
# ``torch_out`` is the output after executing the model. Normally you can
# ignore this output, but here we will use it to verify that the model we
# exported computes the same values when run in onnxruntime.
#
# But before verifying the model's output with onnxruntime, we will check
# the onnx model with onnx's API. This will verify the model's structure
# and confirm that the model has a valid schema. 

import onnx

onnx_model = onnx.load("super_resolution.onnx")
onnx.checker.check_model(onnx_model)


######################################################################
# Now let's create an onnxruntime session. This part can normally be
# done in a separate process or on another machine, but we will
# continue in the same process so that we can verify that onnxruntime
# and PyTorch are computing the same value for the network:
#

import onnxruntime

ort_session = onnxruntime.InferenceSession("super_resolution.onnx")

def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

# compute onnxruntime output prediction
ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(x)}
ort_outs = ort_session.run(None, ort_inputs)

# compare onnxruntime and PyTorch results
np.testing.assert_allclose(to_numpy(torch_out), ort_outs[0], rtol=1e-03, atol=1e-05)

print("Exported model has been tested with ONNXRuntime, and the result looks good!")


######################################################################
# We should see that the output of PyTorch and onnxruntime runs match
# numerically with the given precision (rtol=1e-03 and atol=1e-05).
# As a side-note, if they do not match then there is an issue in the
# onnx exporter, so please contact us in that case.
#


######################################################################
# Transfering SRResNet using ONNX
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#


######################################################################
# Using the same process as above, we also transferred an interesting new
# model "SRResNet" for super-resolution presented in `this
# paper <https://arxiv.org/pdf/1609.04802.pdf>`__ (thanks to the authors
# at Twitter for providing us code and pretrained parameters for the
# purpose of this tutorial). The model definition and a pre-trained model
# can be found
# `here <https://gist.github.com/prigoyal/b245776903efbac00ee89699e001c9bd>`__.
# Below is what SRResNet model input, output looks like. |SRResNet|
#
# .. |SRResNet| image:: /_static/img/SRResNet.png
#


######################################################################
# Running the model using ONNXRuntime
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#


######################################################################
# So far we have exported a model from PyTorch and shown how to load it
# and run it in onnxruntime with a dummy tensor as an input.

######################################################################
# For this tutorial, we will use a famous cat image used widely which
# looks like below
#
# .. figure:: /_static/img/cat_224x224.jpg
#    :alt: cat
#

######################################################################
# First, let's load the image, pre-process it using standard PIL
# python library. Note that this preprocessing is the standard practice of
# processing data for training/testing neural networks.
#

from PIL import Image
import torchvision.transforms as transforms

img = Image.open("./_static/img/cat.jpg")

resize = transforms.Resize([224, 224])
img = resize(img)

img_ycbcr = img.convert('YCbCr')
img_y, img_cb, img_cr = img_ycbcr.split()

to_tensor = transforms.ToTensor()
img_y = to_tensor(img_y)
img_y.unsqueeze_(0)


######################################################################
# Now, as a next step, let's take the resized cat image and run the
# super-resolution model in ONNXRuntime.
#

ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(img_y)}
ort_outs = ort_session.run(None, ort_inputs)
img_out_y = ort_outs[0]


######################################################################
# At this point, the output of the model is a tensor.
# Now, we'll process the output of the model to construct back the
# final output image from the output tensor, and save the image.
# The post-processing steps have been adopted from PyTorch
# implementation of super-resolution model
# `here <https://github.com/pytorch/examples/blob/master/super_resolution/super_resolve.py>`__
# 

img_out_y = Image.fromarray(np.uint8((img_out_y[0] * 255.0).clip(0, 255)[0]), mode='L')

# get the output image follow post-processing step from PyTorch implementation
final_img = Image.merge(
    "YCbCr", [
        img_out_y,
        img_cb.resize(img_out_y.size, Image.BICUBIC),
        img_cr.resize(img_out_y.size, Image.BICUBIC),
    ]).convert("RGB")

# Save the image, we will compare this with the output image from mobile device
final_img.save("./_static/img/cat_superres_with_ort.jpg")


######################################################################
# .. figure:: /_static/img/cat_superres_with_ort.png
#    :alt: output\_cat
#
#
# ONNXRuntime being a cross platform engine, you can run it across
# multiple platforms and on both CPUs and GPUs.
# 
# ONNXRuntime is high performant. 
# More information `here <https://github.com/microsoft/onnxruntime#high-performance>`__.

# ONNXRuntime can also be deployed to the cloud for model inferencing
# using Azure Machine Learning Services.
# More information `here <https://docs.microsoft.com/en-us/azure/machine-learning/service/concept-onnx>`__.
# 
# For more information about ONNXRuntime `here <https://github.com/microsoft/onnxruntime>`__.
#