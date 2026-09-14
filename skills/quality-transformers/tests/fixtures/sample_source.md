<!--Copyright 2025 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

⚠️ Note that this file is in Markdown but contains specific syntax for our doc-builder (similar to MDX) that may not be
rendered properly in your Markdown viewer.

-->

# Tokenizer[[tokenizer]]

[[open-in-colab]]

A tokenizer converts text into an array of numbers. This guide shows how to load a tokenizer with [`AutoTokenizer`].

> [!WARNING]
> This API is experimental and may change at any time.

## Load a tokenizer[[load-a-tokenizer]]

Use [`AutoTokenizer.from_pretrained`] to load a tokenizer.

<hfoptions id="tokenizer">
<hfoption id="PyTorch">

```py
from transformers import AutoTokenizer

# Load the tokenizer for BERT
tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")
```

</hfoption>
</hfoptions>

Set `HF_TOKEN` before you start. See the [installation guide](../installation) for details.

## API[[transformers.AutoTokenizer]]

[[autodoc]] AutoTokenizer
