<!--Copyright 2025 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

⚠️ Note that this file is in Markdown but contains specific syntax for our doc-builder (similar to MDX) that may not be
rendered properly in your Markdown viewer.

-->

# 토크나이저[[tokenizer]]

[[open-in-colab]]

토크나이저는 텍스트를 숫자 배열로 변환합니다. 이 가이드에서는 [`AutoTokenizer`]로 토크나이저를 가져오는 방법을 살펴봅니다.

> [!WARNING]
> 이 API는 실험적이며 언제든지 변경될 수 있습니다.

## 토크나이저 가져오기[[load-a-tokenizer]]

[`AutoTokenizer.from_pretrained`]으로 토크나이저를 가져오세요.

<hfoptions id="tokenizer">
<hfoption id="PyTorch">

```py
from transformers import AutoTokenizer

# BERT용 토크나이저를 가져옵니다
tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")
```

</hfoption>
</hfoptions>

시작하기 전에 `HF_TOKEN`을 설정하세요. 자세한 내용은 [설치 가이드](../installation)를 참고하세요.

## API[[transformers.AutoTokenizer]]

[[autodoc]] AutoTokenizer
