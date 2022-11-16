Dynamo Troubleshooting Guide
============================
**Author**: `Michael Lazos <https://github.com/mlazos>`_



Table of Contents
=================

-  `Introduction <#introduction>`__
-  `Guide to Diagnosing Runtime
   Errors <#guide-to-diagnosing-runtime-errors>`__

   -  `Torchdynamo Errors <#torchdynamo-errors>`__
   -  `TorchInductor Errors <#torchinductor-errors>`__
   -  `Minifying TorchInductor
      Errors <#minifying-torchinductor-errors>`__
   -  `Minifying Backend Compiler
      Errors <#minifying-backend-compiler-errors>`__

-  `Performance Profiling <#performance-profiling>`__

   -  `Accessing TorchDynamo
      Profiler <#accessing-torchdynamo-profiler>`__
   -  `TorchInductor Debug Tracing <#torchinductor-debug-tracing>`__
   -  `Memory Profiling <#memory-profiling>`__
   -  `Graph Breaks <#graph-breaks>`__

      -  `Identifying the cause of a graph
         break <#identifying-the-cause-of-a-graph-break>`__

   -  `Excessive Recompilation <#excessive-recompilation>`__

-  `Accuracy Debugging <#accuracy-debugging>`__
-  `File an Issue <#file-an-issue>`__

Introduction
============

TorchDynamo is still in active development, and many of the reasons for
graph breaks and excessive recompilation will be fixed with upcoming
support for `tracing dynamic tensor
shapes <https://docs.google.com/document/d/1QJB-GOnbv-9PygGlOMXwiO9K6vVNm8sNg_olixJ9koc/edit?usp=sharing>`__,
more careful choices for guards and better tuned heurstics.

In the mean time, you may need to diagnose a particular issue and
determine if it is easy to work around with a change to your model, or
file an issue for support.

We’re also actively developing debug tools, profilers, and improving our
errors/warnings. Please give us feedback if you have an issue with this
infra, or an idea for an improvement. Below is a table of the available
tools and their typical usage. For additional help see the next section.
\| Tool \| Purpose \| Usage \| \| ———————————– \|
—————————————————————————————————————————- \| —————————————————————————-
\| \| Info logging \| View summarized steps of compilation \|
``torch._dynamo.config.log_level = logging.INFO`` \| Debug logging \|
View detailed steps of compilation (print every instruction traced) \|
``torch._dynamo.config.log_level = logging.DEBUG`` and
``torch._dynamo.config.verbose = True`` \| \| Minifier for any backend
\| Find smallest subgraph which reproduces errors for any backend \| set
environment variable TORCHDYNAMO_REPRO_AFTER=“dynamo” \| \| Minifier for
TorchInductor \| If the error is known to occur after AOTAutograd find
smallest subgraph wich reproduces errors during TorchInductor lowering
\| set environment variable TORCHDYNAMO_REPRO_AFTER=“aot” \| \| Accuracy
minifier \| Finds the smallest subgraph which reproduces an accuracy
issue between an eager model model and optimized model \|
``TORCHDYNAMO_REPRO_AFTER=<"aot"/"dynamo"> TORCHDYNAMO_REPRO_LEVEL=4``
\| \| ``torch._dynamo.explain`` \| Find graph breaks and display
reasoning for them \| ``torch._dynamo.explain(fn, *inputs)`` \| \|
Record/Replay \| Record and replay frames which to reproduce errors
during graph capture \|
``torch._dynamo.config.replay_record_enabled = True`` \| \| TorchDynamo
function name filtering \| only compile functions with the given name to
reduce noise when debugging an issue \| set environment variable
TORCHDYNAMO_DEBUG_FUNCTION=<name> \| \| TorchInductor Debug logging \|
Print general TorchInductor debug info and generated Triton/C++ code \|
``torch._inductor.config.debug = True`` \| \| TorchInductor Tracing \|
Show time taken in each TorchInductor stage + output code and graph
visualization \| set the environment variable TORCHINDUCTOR_TRACE=1 or
``torch._inductor.config.trace.enabled = True`` \| s \|

Guide to Diagnosing Runtime Errors
==================================

Below is the TorchDynamo compiler stack.

At a high level, the TorchDynamo stack consists of a graph capture from
Python code (TorchDynamo) and a backend compiler. In this example the
backend compiler consists of backward graph tracing (AOTAutograd) and
graph lowering (TorchInductor)*. Errors can occur in any component of
the stack and will provide full stack traces.

You may use info logging
(``torch._dynamo.config.log_level = logging.INFO``) and look for
``Step #: ...`` outputs in order to determine in which component the
error occurred in. Logs are made at the beginning and end of each step,
so the step that an error should correspond to is the most recent logged
step whose end has not yet been logged. The steps correspond to the
following parts of the stack (according to the image above):

==== ================
Step Component
==== ================
1    TorchDynamo
2    Compiler Backend
3    TorchInductor
==== ================

The beginning and end of AOTAutograd is currently not logged, but we
plan to add it soon.

If info logging is insufficient, then there are also some backend
options which can enable you to determine which component is causing the
error if you’re unable to understand the error message that is
generated. These are the following:

-  ``"eager"``: only runs torchdynamo forward graph capture and then
   runs the captured graph with PyTorch. This provides an indication as
   to whether TorchDynamo is raising the error.

-  ``"aot_eager"``: runs torchdynamo to capture a forward graph, and
   then AOTAutograd to trace the backward graph without any additional
   backend compiler steps. PyTorch eager will then be used to run the
   forward and backward graphs. This is useful to narrow down the issue
   to AOTAutograd.

The general procedure to narrow down an issue is the following: 1. Run
your program with the ``"eager"`` backend. If the error no longer
occurs, the issue is in the backend compiler that is being used (if
using TorchInductor, proceed to step 2, if not, see `this
section <#minifying-backend-compiler-errors>`__). If the error still
occurs with the ``"eager"`` backend, it is an `error while running
torchdynamo <#torchdynamo-errors>`__.

2. This step is only necessary if TorchInductor is used as the backend
   compiler. Run the model with the ``"aot_eager"`` backend. If this
   backend raises an error then the error is occurring during
   AOTAutograd tracing. If the error no longer occurs with this backend,
   then `the error is in
   TorchInductor\* <#minifying-torchinductor-errors>`__.

Each of these cases are analyzed in the following sections.

\*Note on TorchInductor naming: The TorchInductor backend consists of
both AOTAutograd tracing and the TorchInductor compiler itself. We will
disambiguate by referring to TorchInductor as the backend, and
TorchInductor lowering as the phase which lowers the graph traced by
AOTAutograd.

Torchdynamo Errors
------------------

If the error that is generated occurs with the ``"eager"`` backend, then
torchdynamo is the most likely source of the error. Here is example code
which will generate an error.

.. code:: py

   import torch

   import torch._dynamo as dynamo


   @dynamo.optimize("eager")
   def test_assertion_error():
       y = torch.ones(200, 200)
       z = {y: 5}
       return z


   test_assertion_error()

Which will generate the following error:

::

   torch._dynamo.convert_frame: [ERROR] WON'T CONVERT test_assertion_error /scratch/mlazos/torchdynamo/../test/errors.py line 26 
   due to: 
   Traceback (most recent call last):
     File "/scratch/mlazos/torchdynamo/torchdynamo/symbolic_convert.py", line 837, in BUILD_MAP
       assert isinstance(k, ConstantVariable) or (
   AssertionError

   from user code:
      File "/scratch/mlazos/torchdynamo/../test/errors.py", line 34, in test_assertion_error
       z = {y: 5}

   Set torch._dynamo.config.verbose=True for more information
   ==========

As the message suggests you can set
``torch._dynamo.config.verbose=True`` to get a full stack trace to both
the error in torchdynamo and the user code. In addition to this flag,
you can also set the ``log_level`` of torchdynamo through
``torch._dynamo.config.log_level``. The available levels are the
following: - ``logging.DEBUG``: Print every instruction that is
encountered in addition to all below log levels - ``logging.INFO``:
Print each function that is compiled (original and modified bytecode)
and the graph that is captured in addition to all below log levels -
``logging.WARNING`` (default): Print graph breaks in addition to all
below log levels - ``logging.ERROR``: Print errors only

If a model is sufficiently large, the logs can become overwhelming. If
an error occurs deep within a model’s python code, it can be useful to
execute only the frame in which the error occurs to enable easier
debugging. There are two tools available to enable this: - Setting the
environment variable TORCHDYNAMO_DEBUG_FUNCTION to the desired function
name will only run torchdynamo on functions with that name. - There is a
record/replay tool (set
``torch._dynamo.config.replay_record_enabled = True``) which dumps an
execution record when an error is encountered. This record can then be
replayed to run only the frame where an error occurred.

TorchInductor Errors
--------------------

If the error doesn’t occur with the ``"eager"`` backend, then the
backend compiler is the source of the error (`example
error <https://gist.github.com/mlazos/2f13681e3cc6c43b3911f336327032de%5D>`__).
There are `different
choices <https://github.com/pytorch/torchdynamo/blob/0b8aaf340dad4777a080ef24bf09623f1aa6f3dd/README.md#existing-backends>`__
for backend compilers for torchdynamo, with TorchInductor or nvfuser
fitting the needs of most users. This section focuses on TorchInductor
as the motivating example, but some tools will be usable with other
backend compilers.

Below is the portion of the stack which we are focusing on:

With TorchInductor as the chosen backend, AOTAutograd is used to
generate the backward graph from the forward graph captured by
torchdynamo. It’s important to note that errors can occur during this
tracing and also while TorchInductor lowers the forward and backward
graphs to GPU code or C++. A model can often consist of hundreds or
thousands of FX nodes, so narrowing the exact nodes where this problem
occurred can be very difficult. Fortunately, there are tools availabe to
automatically minify these input graphs to the nodes which are causing
the issue. The first step is to determine whether the error occurs
during tracing of the backward graph with AOTAutograd or during
TorchInductor lowering. As mentioned above in step 2, the
``"aot_eager"`` backend can be used to run only AOTAutograd in isolation
without lowering. If the error still occurs with this backend, this
indicates that the error is occurring during AOTAutograd tracing.

Here’s an example:

.. code:: py

   import torch

   import torch._dynamo as dynamo

   model = torch.nn.Sequential(*[torch.nn.Linear(200, 200) for _ in range(5)])

   @dynamo.optimize("inductor")
   def test_backend_error():

       y = torch.ones(200, 200)
       x = torch.ones(200, 200)
       z = x + y
       a = torch.ops.aten._foobar(z)  # dummy function which errors
       return model(a)


   test_backend_error()

Running this should give you this error (with a longer stack trace below
it)

::

   Traceback (most recent call last):
     File "/scratch/mlazos/torchdynamo/torchinductor/graph.py", line 246, in call_function
       return lowerings[target](*args, **kwargs)
     File "/scratch/mlazos/torchdynamo/torchinductor/lowering.py", line 185, in wrapped
       return decomp_fn(*args, **kwargs)
     File "/scratch/mlazos/torchdynamo/torchinductor/lowering.py", line 810, in _foobar
       assert False
   AssertionError

   ... 

`error with full stack
trace <https://gist.github.com/mlazos/d6947854aa56d686800259a164c62100>`__

If you then change ``@dynamo.optimize("inductor")`` to
``@dynamo.optimize("aot_eager")``, it will run without error, because
`the
issue <https://github.com/pytorch/torchdynamo/blob/d09e50fbee388d466b5252a63045643166006f77/torchinductor/lowering.py#:~:text=%23%20This%20shouldn%27t%20be,assert%20False>`__
is in the TorchInductor lowering process, not in AOTAutograd.

Minifying TorchInductor Errors
------------------------------

From here, let’s run the minifier to get a minimal repro. Setting the
environment variable TORCHDYNAMO_REPRO_AFTER=“aot” (or setting
``torch._dynamo.config.repro_after="aot"`` directly) will generate a
python program which reduces the graph produced by AOTAutograd to the
smallest subgraph which reproduces the error. (See below for an example
where we minify the graph produced by torchdynamo) Running the program
with this environment variable should show nearly `identical
output <https://gist.github.com/mlazos/0458ab828aa403c779fe73c012aa5982>`__,
with an additional line indicating where ``minifier_launcher.py`` has
been written to. The output directory is configurable by setting
``torch._dynamo.config.base_dir`` to a valid directory name. The final
step is to run the minifier and check that it runs successfully. A
successful run looks like
`this <https://gist.github.com/mlazos/e6ea41ccce68a7b1b8a7a09acb1b206a>`__.
If the minifier runs successfully, it generates runnable python code
which reproduces the exact error. For our example this is the following
code:

.. code:: py

   import torch
   from torch import tensor, device
   import torch.fx as fx
   from torch._dynamo.testing import rand_strided
   from math import inf
   from torch.fx.experimental.proxy_tensor import make_fx

   # torch version: 1.13.0a0+gitfddfc44
   # torch cuda version: 11.6
   # torch git version: fddfc4488afb207971c54ad4bf58130fdc8a4dc5


   # CUDA Info: 
   # nvcc: NVIDIA (R) Cuda compiler driver 
   # Copyright (c) 2005-2022 NVIDIA Corporation 
   # Built on Thu_Feb_10_18:23:41_PST_2022 
   # Cuda compilation tools, release 11.6, V11.6.112 
   # Build cuda_11.6.r11.6/compiler.30978841_0 

   # GPU Hardware Info: 
   # NVIDIA A100-SXM4-40GB : 8 


   from torch.nn import *
   class Repro(torch.nn.Module):
       def __init__(self):
           super().__init__()

       
       
       def forward(self, add):
           _foobar = torch.ops.aten._foobar.default(add);  add = None
           return (_foobar,)
           
   args = [((200, 200), (200, 1), torch.float32, 'cpu')]
   args = [rand_strided(shape, stride, dtype, device) for shape, stride, dtype, device in args]
   mod = make_fx(Repro())(*args)

   from torch._inductor.compile_fx import compile_fx_inner

   compiled = compile_fx_inner(mod, args)
   compiled(*args)

The ``forward`` method of the ``Repro`` module contains the exact op
which causes the issue. When filing an issue, please include any
minified repros to aid in debugging.

Minifying Backend Compiler Errors
---------------------------------

With backend compilers other than TorchInductor the process for finding
the subgraph causing the error is nearly identical to the procedure in
`errors in TorchInductor <#torchinductor-errors>`__ with one important
caveat. Namely, that the minifier will now be run on the graph that is
traced by TorchDynamo, not the output graph of AOTAutograd. Let’s walk
through an example.

.. code:: py

   import torch

   import torch._dynamo as dynamo

   model = torch.nn.Sequential(*[torch.nn.Linear(200, 200) for _ in range(5)])

   # toy compiler which fails if graph contains relu
   def toy_compiler(gm: torch.fx.GraphModule, _):
       for node in gm.graph.nodes:
           if node.target == torch.relu:
               assert False

       return gm


   @dynamo.optimize(toy_compiler)
   def test_backend_error():
       y = torch.ones(200, 200)
       x = torch.ones(200, 200)
       z = x + y
       a = torch.relu(z)
       return model(a)


   test_backend_error()

In order to run the code after TorchDynamo has traced the forward graph,
the TORCHDYNAMO_REPRO_AFTER enviornment variable can be used. Running
this program with TORCHDYNAMO_REPRO_AFTER=“dynamo” (or
``torch._dynamo.config.repro_after="dynamo"``) should produce `this
output <https://gist.github.com/mlazos/244e3d5b53667e44078e194762c0c92b>`__\ and
the following code in ``{torch._dynamo.config.base_dir}/repro.py``.
Note: the other option for TORCHDYNAMO_REPRO_AFTER are ``"aot"``, which
will run the minifier after the backward graph has been generated.

.. code:: py

   import torch
   import torch._dynamo as dynamo
   from torch import tensor, device
   import torch.fx as fx
   from torch._dynamo.testing import rand_strided
   from math import inf
   from torch._dynamo.debug_utils import run_fwd_maybe_bwd


   from torch.nn import *
   class Repro(torch.nn.Module):
       def __init__(self):
           super().__init__()

       
       
       def forward(self, add):
           relu = torch.relu(add);  add = None
           return (relu,)
           

   mod = Repro().cuda()
   opt_mod = dynamo.optimize("None")(mod)


   args = [((200, 200), (200, 1), torch.float32, 'cpu', False)]
   args = [rand_strided(sh, st, dt, dev).requires_grad_(rg) for (sh, st, dt, dev, rg) in args]


   with torch.cuda.amp.autocast(enabled=False):
       ref = run_fwd_maybe_bwd(mod, args)
       res = run_fwd_maybe_bwd(opt_mod, args)

The minifier successfully reduced the graph to the op that raises the
error in ``toy_compiler``. The other difference from the procedure in
`TorhInductor Errors <#torchinductor-errors>`__ is that the minifier is
automatically run after encountering a backend compiler error. After a
successful run, the minifier writes ``repro.py`` to
``torch._dynamo.config.base_dir``.

Performance Profiling
=====================

Accessing TorchDynamo Profiler
------------------------------

TorchDynamo has a builtin stats function for collecting and displaying
the time spent in each compilation phase. These stats can be accessed by
calling ``torch._dynamo.utils.compile_times()`` after executing
Torch._Dynamo. By default, this returns a string representation of the
compile times spent in each TorchDynamo function by name.

TorchInductor Debug Tracing
---------------------------

TorchInductor has a builtin stats and trace function for displaying time
spent in each compilation phase, output code, output graph visualization
and IR dump. This is a debugging tool designed to make it easier to
debug/understand the internals of TorchInductor.

Setting the environment variable ``TORCHINDUCTOR_TRACE=1`` will cause a
debug trace directory to be created and printed:

::

   $ env TORCHINDUCTOR_TRACE=1 python repro.py
   torch._inductor.debug: [WARNING] model_forward_0 debug trace: /tmp/torchinductor_jansel/rh/crhwqgmbqtchqt3v3wdeeszjb352m4vbjbvdovaaeqpzi7tdjxqr.debug

Here is an `example debug directory
output <https://gist.github.com/jansel/f4af078791ad681a0d4094adeb844396>`__
for the test program:

::

   torch.nn.Sequential(
           torch.nn.Linear(10, 10),
           torch.nn.LayerNorm(10),
           torch.nn.ReLU(),
       )

Note each file in that debug trace can be enabled/disabled via
``torch._inductor.config.trace.*``. The profile and the diagram are both
disabled by default since they are expensive to generate.

A single node in this new debug format looks like:

::

   buf1: SchedulerNode(ComputedBuffer)
   buf1.writes = 
       {   MemoryDep(name='buf1', index=0, size=()),
           MemoryDep(name='buf1', index=0, size=(s0,))}
   buf1.unmet_dependencies = {MemoryDep(name='buf0', index=c0, size=(s0,))}
   buf1.met_dependencies = {MemoryDep(name='primals_2', index=c0, size=(s0,))}
   buf1.group.device = cuda:0
   buf1.group.iteration = (1, s0)
   buf1.sizes = ([], [s0])
   class buf1_loop_body:
       var_ranges = {z0: s0}
       index0 = z0
       index1 = 0
       def body(self, ops):
           get_index = self.get_index('index0')
           load = ops.load('buf0', get_index, False)
           get_index_1 = self.get_index('index0')
           load_1 = ops.load('primals_2', get_index_1, False)
           add = ops.add(load, load_1)
           get_index_2 = self.get_index('index1')
           reduction = ops.reduction('buf1', torch.float32, torch.float32, 'sum', get_index_2, add)
           return reduction

See the `example debug directory
output <https://gist.github.com/jansel/f4af078791ad681a0d4094adeb844396>`__
for more examples.

Memory Profiling
----------------

TBD

Graph Breaks
------------

Given a program like this,

.. code:: py

   @dynamo.optimize(...)
   def some_fun(x):
       ...

   some_fun(x)
   ...

Torchdynamo will attempt to compile all of the torch/tensor operations
within some_fun into a single FX graph, but it may fail to capture
everything into one graph.

Some graph break reasons are insurmountable to TorchDynamo, and can’t be
easily fixed. - calling into a C extension other than torch is invisible
to torchdynamo, and could do arbitrary things without TorchDynamo being
able to introduce necessary `guards <./GuardsOverviewPt1.md>`__ to
ensure that the compiled program would be safe to reuse. Graph breaks
can hinder performance if the resulting fragments are small. To maximize
performance, it’s important to have as few graph breaks as possible.

Identifying the cause of a graph break
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To identify all graph breaks in a program and the associated reasons for
the breaks, ``torch._dynamo.explain`` can be used. This tool runs
TorchDynamo on the supplied function and aggregates the graph breaks
that are encountered. Here is an example usage:

.. code:: py

   import torch
   import torch._dynamo as dynamo

   def toy_example(a, b):
       x = a / (torch.abs(a) + 1)
       print("woo")
       if b.sum() < 0:
           b = b * -1
       return x * b


   explanation, out_guards, graphs, ops_per_graph = dynamo.explain(toy_example, torch.randn(10), torch.randn(10))
   print(explanation)

   """
   Dynamo produced 3 graphs, with 2 graph break and 6 ops. 
    Break reasons: 

   1. call_function BuiltinVariable(print) [ConstantVariable(str)] {} 
      File "t2.py", line 16, in toy_example
       print("woo")
    
   2. generic_jump 
      File "t2.py", line 17, in toy_example
       if b.sum() < 0:
    """

Note on other outputs: - ``out_guards`` - a list of lists where each
sublist contains the guards that must pass to ensure the traced graphs
are valid - ``graphs`` - a list of graph modules which were successfully
traced - ``ops_per_graph`` - a list of lists where each sublist contains
the ops thatare run in the graph

To throw an error on the first graph break encountered, ``nopython``
mode can be used. This disables TorchDynamo’s python fallback, and only
succeeds if the entire program is convertible to a single graph. Example
usage:

.. code:: py

   @dynamo.optimize(<compiler>, nopython=True)
   def toy_example(a, b):
      ...

Excessive Recompilation
-----------------------

When TorchDynamo compiles a function (or part of one), it makes certain
assumptions about locals and globals in order to allow compiler
optimizations, and expresses these assumptions as guards that check
particular values at runtime. If any of these guards fail, Dynamo will
recompile that function (or part) up to
``torch._dynamo.config.cache_size_limit`` times. If your program is
hitting the cache limit, you will first need to determine which guard is
failing and what part of your program is triggering it.

The `recompilation profiler <#recompilation-profiler>`__ automates the
process of setting TorchDynamo’s cache limit to 1 and running your
program under an observation-only ‘compiler’ that records the causes of
any guard failures. You should be sure to run your program for at least
as long (as many iterations) as you were running when you ran into
trouble, and the profiler will accumulate statistics over this duration.

If your program exhibits a bounded amount of dynamism, you may be able
to tune the TorchDynamo cache limit to allow for each variation to be
compiled and cached, but if the cache limit is too high you may find the
cost of recompilation outweighs any optimization benefits.

::

   torch._dynamo.config.cache_size_limit = <your desired cache limit>

Torchdynamo plans to support many common cases of dynamic tensor shapes,
such as varying batch size or sequence length. It does not plan to
support rank-dynamism. In the mean time, setting a specific cache limit
can be used in coordination with bucketing techniques to achieve an
acceptable number of recompilations for some dynamic models.

.. code:: py

   prof = dynamo.utils.CompilationProfiler()

   @dynamo.optimize(prof)
   def my_model():
       ...

   my_model()
   print(prof.report())

Accuracy Debugging
==================

Accuracy issues can also be minified if you set the environment variable
``TORCHDYNAMO_REPRO_LEVEL=4``, it operates with a similar git bisect
model and a full repro might be something like
``TORCHDYNAMO_REPRO_AFTER="aot" TORCHDYNAMO_REPRO_LEVEL=4`` the reason
we need this is downstream compilers will codegen code whether it’s
Triton code or the C++ backend, the numerics from those downstream
compilers can be different in subtle ways yet have dramatic impact on
your training stability. So the accuracy debugger is very useful for us
to detect bugs in our codegen or with a backend compiler.

File an Issue
=============

You should feel encouraged to `file a github
issue <https://github.com/pytorch/torchdynamo/issues>`__ and expect a
timely response.

Before filing an issue, read over the `README <../README.md>`__,
`TROUBLESHOOTING <./TROUBLESHOOTING.md>`__, and search for similar
issues.

When filing an issue, please include - your
OS/python/pytorch/CUDA/triton info by running:

.. code:: shell

   python tools/verify_install.py

-  a minimal repro script if possible, which can be generated by running
   Minifier
-  a description of the error
-  the expected behavior
-  a log (set ``torch._dynamo.config.log_file`` to a valid file name to
   dump the logs to a file and
   ``torch._dynamo.config.log_level = logging.DEBUG`` and
   ``torch._dynamo.config.verbose = True``)
