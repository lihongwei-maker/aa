Welcome to PyTorch Tutorials
============================

.. raw:: html

    <div class="tutorials-callout-container">
        <div class="row">

.. Add callout items below this line

.. customcalloutitem::
   :description: The 60 min blitz is the most common starting point and provides a broad view on how to use PyTorch. It covers the basics all to the way constructing deep neural networks. 
   :header: New to PyTorch?
   :button_link: beginner/deep_learning_60min_blitz.html
   :button_text: Start 60-min blitz

.. customcalloutitem::
   :description: Bite-sized, ready-to-deploy PyTorch code examples. 
   :header: Recipes
   :button_link: recipes/recipe_index.html
   :button_text: Explore Recipes

.. End of callout item section

.. raw:: html

        </div>
    </div>

    <div id="tutorial-cards-container">

    <nav class="navbar navbar-expand-lg navbar-light tutorials-nav col-12">
        <div class="tutorial-tags-container">
            <div id="dropdown-filter-tags">
                <div class="tutorial-filter-menu">
                    <div class="tutorial-filter filter-btn all-tag-selected" data-tag="all">All</div>
                </div>
            </div>
        </div>
    </nav>

    <hr class="tutorials-hr">

    <div class="row">

    <div id="tutorial-cards">
    <div class="list">

.. Add tutorial cards below this line

.. Learning PyTorch

.. customcarditem::
   :header: Deep Learning with PyTorch: A 60 Minute Blitz
   :card_description: Understand PyTorch’s Tensor library and neural networks at a high level.
   :image: _static/img/thumbnails/pytorch-logo-flat.png
   :link: beginner/deep_learning_60min_blitz.html
   :tags: Getting-Started

.. customcarditem::
   :header: Learning PyTorch with Examples
   :card_description: This tutorial introduces the fundamental concepts of PyTorch through self-contained examples.
   :image: _static/img/thumbnails/examples.png
   :link: beginner/pytorch_with_examples.html
   :tags: Getting-Started

.. customcarditem::
   :header: What is torch.nn really?
   :card_description: Use torch.nn to create and train a neural network.
   :image: _static/img/torch.nn.png
   :link: beginner/nn_tutorial.html
   :tags: Getting-Started

.. customcarditem::
   :header: Visualizing Models, Data, and Training with Tensorboard
   :card_description: Learn to use TensorBoard to visualize data and model training.
   :image: _static/img/thumbnails/pytorch_tensorboard.png
   :link: intermediate/tensorboard_tutorial.html
   :tags: Interpretability, Getting-Started, Tensorboard

.. Image/Video

.. customcarditem::
   :header: TorchVision Object Detection Finetuning Tutorial
   :card_description: Finetune a pre-trained Mask R-CNN model.
   :image: _static/img/thumbnails/tv-img.png
   :link: intermediate/torchvision_tutorial.html
   :tags: Image/Video

.. customcarditem::
   :header: Transfer Learning for Computer Vision Tutorial
   :card_description: Train a convolutional neural network for image classification using transfer learning. 
   :image: _static/img/thumbnails/sphx_glr_transfer_learning_tutorial_001.png
   :link: beginner/transfer_learning_tutorial.html
   :tags: Image/Video

.. customcarditem::
   :header: Adversarial Example Generation
   :card_description: Train a convolutional neural network for image classification using transfer learning. 
   :image: _static/img/panda.png
   :link: beginner/fgsm_tutorial.html
   :tags: Image/Video

.. customcarditem::
   :header: DCGAN Tutorial
   :card_description: Train a generative adversarial network (GAN) to generate new celebrities.
   :image: _static/img/dcgan_generator.png
   :link: beginner/dcgan_faces_tutorial.html
   :tags: Image/Video

.. customcarditem::
   :header: (Experimental) Static Quantization with Eager Mode in PyTorch
   :card_description: Learn techniques to impove a model's accuracy =  post-training static quantization, per-channel quantization, and quantization-aware training. 
   :image: _static/img/qat.png
   :link: advanced/static_quantization_tutorial.html
   :tags: Image/Video, Quantization, Model-Optimization

.. customcarditem::
   :header: (Experimental) Quantized Transfer Learning for Computer Vision Tutorial
   :card_description: Learn techniques to impove a model's accuracy -  post-training static quantization, per-channel quantization, and quantization-aware training. 
   :image: _static/img/qat.png
   :link: advanced/static_quantization_tutorial.html
   :tags: Image/Video, Quantization, Model-Optimization

.. Audio

.. customcarditem::
   :header: torchaudio Tutorial
   :card_description: Learn to load and preprocess data from a simple dataset with PyTorch's torchaudio library. 
   :image: _static/img/audio_preprocessing_tutorial_waveform.png
   :link: beginner/audio_preprocessing_tutorial.html
   :tags: Audio

.. Text

.. customcarditem::
   :header: Sequence-to-Sequence Modeling wiht nn.Transformer and torchtext
   :card_description: Learn how to train a sequence-to-sequence model that uses the nn.Transformer module. 
   :image: _static/img/transformer_architecture.jpg
   :link: beginner/transformer_tutorial.html
   :tags: Text

.. customcarditem::
   :header: NLP from Scratch: Classifying Names with a Character-level RNN
   :card_description: Build and train a basic character-level RNN to classify word from scratch without the use of torchtext. First in a series of three tutorials. 
   :image: _static/img/rnnclass.png
   :link: intermediate/char_rnn_classification_tutorial
   :tags: Text

.. customcarditem::
   :header: NLP from Scratch: Generating Names with a Character-level RNN
   :card_description: After using character-level RNN to classify names, leanr how to generate names from languages. Second in a series of three tutorials. 
   :image: _static/img/char_rnn_generation.png
   :link: intermediate/char_rnn_generation_tutorial.html
   :tags: Text

.. customcarditem::
   :header: NLP from Scratch: Translation with a Sequence-to-sequence Network and Attention 
   :card_description: This is the third and final tutorial on doing “NLP From Scratch”, where we write our own classes and functions to preprocess the data to do our NLP modeling tasks.
   :image: _static/img/seq2seq_flat.png
   :link: intermediate/seq2seq_translation_tutorial.html
   :tags: Text

.. customcarditem::
   :header: Text Classification with Torchtext
   :card_description: This is the third and final tutorial on doing “NLP From Scratch”, where we write our own classes and functions to preprocess the data to do our NLP modeling tasks.
   :image: _static/img/text_sentiment_ngrams_model.png
   :link: beginner/text_sentiment_ngrams_tutorial.html
   :tags: Text

.. customcarditem::
   :header: Language Translation with Torchtext
   :card_description: Use torchtext to reprocess data from a well-known datasets containing both English and German. Then use it to train a sequence-to-sequence model.  
   :image: _static/img/thumbnails/german_to_english_translation.png
   :link: beginner/torchtext_translation_tutorial.html
   :tags: Text

.. customcarditem::
   :header: (Experimental) Dynamic Quantization on an LSTM Word Language Model
   :card_description: Apply dynamic quantization, the easiest form of quantization, to a LSTM-based next word prediction model.  
   :image: _static/img/quant_asym.png
   :link: advanced/dynamic_quantization_tutorial.html
   :tags: Text, Quantization, Model-Optimization

.. customcarditem::
   :header: (Experimental) Dynamic Quantization on BERT
   :card_description: Apply the dynamic quantization on a BERT (Bidirectional Embedding Representations from Transformers) model. 
   :image: _static/img/bert.png
   :link: intermediate/dynamic_quantization_bert_tutorial.html
   :tags: Text, Quantization, Model-Optimization

.. Reinforcement Learning

.. customcarditem::
   :header: Reinforcement Learning (DQN)
   :card_description: Learn how to use PyTorch to train a Deep Q Learning (DQN) agent on the CartPole-v0 task from the OpenAI Gym.
   :image: _static/img/cartpole.gif
   :link: intermediate/reinforcement_q_learning.html
   :tags: Reinforcement-Learning

.. Additional APIs

.. customcarditem::
   :header: Using the PyTorch C++ Frontend
   :card_description: Walk through an end-to-end example of training a model with the C++ frontend by training a DCGAN – a kind of generative model – to generate images of MNIST digits.
   :image: _static/img/cpp-pytorch.png
   :link: advanced/cpp_frontend.html
   :tags: C++


.. customcarditem::
   :header: (Experimental) Introduction to Named Tensors in PyTorch
   :card_description: Learn how to use PyTorch to train a Deep Q Learning (DQN) agent on the CartPole-v0 task from the OpenAI Gym.
   :image: _static/img/named_tensor.png
   :link: intermediate/named_tensor_tutorial.html
   :tags: Named-Tensor, Best-Practice

.. customcarditem::
   :header: Pruning Tutorial
   :card_description: Learn how to use torch.nn.utils.prune to sparsify your neural networks, and how to extend it to implement your own custom pruning technique.
   :image: _static/img/pruning.png
   :link: intermediate/pruning_tutorial.html
   :tags: Model-Optimization, Best-Practice

.. End of tutorial card section

.. raw:: html

    </div>

    </div>

    </div>

    </div>

.. .. galleryitem:: beginner/saving_loading_models.py

Additional Resources
============================

.. raw:: html

    <div class="tutorials-callout-container">
        <div class="row">

.. Add callout items below this line

.. customcalloutitem::
   :header: Examples of PyTorch
   :description: A set of examples around pytorch in Vision, Text, Reinforcement Learning, etc.
   :button_link: https://github.com/pytorch/examples
   :button_text: Check Them Out

.. customcalloutitem::
   :header: Recipes
   :description: Bite-sized, ready-to-deploy PyTorch code examples. 
   :button_link: recipes/recipes_index.html
   :button_text: Explore Recipes

.. customcalloutitem::
   :header: PyTorch Cheat Sheet
   :description: Quick overview to essential PyTorch elements. 
   :button_link: beginner/ptcheat.html
   :button_text: Download

.. customcalloutitem::
   :header: Tutorials on GitHub
   :description: Access PyTorch Tutorials from GitHub. 
   :button_link: https://github.com/pytorch/tutorials
   :button_text: Go To GitHub


.. End of callout section

.. raw:: html

        </div>
    </div>

    <div style='clear:both'></div>

.. -----------------------------------------
.. Page TOC
.. -----------------------------------------
.. toctree::
   :maxdepth: 2
   :hidden:
   :includehidden:
   :caption: Recipes

   recipes/recipes_index

.. toctree::
   :maxdepth: 2
   :hidden:
   :includehidden:
   :caption: Learning PyTorch

   beginner/deep_learning_60min_blitz
   beginner/pytorch_with_examples
   beginner/nn_tutorial
   intermediate/tensorboard_tutorial

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:
   :caption: Image/Video

   intermediate/torchvision_tutorial
   beginner/transfer_learning_tutorial
   beginner/fgsm_tutorial
   beginner/dcgan_faces_tutorial
   advanced/static_quantization_tutorial
   intermediate/quantized_transfer_learning_tutorial

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:
   :caption: Audio

   beginner/audio_preprocessing_tutorial

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:
   :caption: Text

   beginner/transformer_tutorial
   intermediate/char_rnn_classification_tutorial
   intermediate/char_rnn_generation_tutorial
   intermediate/seq2seq_translation_tutorial
   beginner/text_sentiment_ngrams_tutorial
   beginner/torchtext_translation_tutorial
   advanced/dynamic_quantization_tutorial
   intermediate/dynamic_quantization_bert_tutorial

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:
   :caption: Reinforcement Learning

   intermediate/reinforcement_q_learning


.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:
   :caption: Additional APIs

   advanced/cpp_frontend
   intermediate/named_tensor_tutorial
   intermediate/pruning_tutorial
