"""Link-label translation and exact restoration of protected Markdown."""
from collections import Counter
import json

import pytest
from markdown_it import MarkdownIt

from scripts.ecl_translation_pipeline import (
    parse_markdown_blocks,
    protect_inline,
    restore_body,
    restore_inline,
    translate_markdown_with_ecl,
)


def test_translate_label_and_surrounding_sentence_without_changing_target():
    source = 'See [the documentation](https://example.com/path_(v1) "Guide") and run `pip install transformers`.'
    masked, saved = protect_inline(source)
    assert "the documentation" in masked
    assert "https://" not in masked
    translated = masked.replace("See ", "").replace("the documentation", "문서").replace(" and run ", "를 참고하고 ").replace(".", "를 실행하세요.")
    restored = restore_inline(translated, saved)
    assert restored == '[문서](https://example.com/path_(v1) "Guide")를 참고하고 `pip install transformers`를 실행하세요.'


@pytest.mark.parametrize("source", [
    '[a [nested] label](https://example.com/a_(b))',
    '[a `code]inside` label](https://example.com "a ) title")',
    "[label](https://example.com/it's 'title')",
    '[label](<https://example.com/a(b)> "title")',
    r'[escaped \] label](https://example.com/a\(b\))',
    '[empty]()',
    'A ``code with ` inside`` and `a\nb`.',
    r'Escaped \[text\] and unmatched `backtick.',
    '![alt text](https://example.com/image.png "image title")',
    '[![alt](https://example.com/image.png)](https://example.com/page)',
    '<https://example.com/path> <person@example.com> <span class="x">text</span>',
    'See https://example.com/path and `api()`.',
    '[explicit][id] [id][] [id]\n\n[id]: https://example.com "title"\n',
])
def test_exact_round_trip(source):
    masked, saved = protect_inline(source)
    assert restore_inline(masked, saved) == source


def test_code_in_link_label_is_protected_but_description_is_visible():
    masked, saved = protect_inline('Use [`torch.mps.Stream` and the `torch.mps.stream` context manager](https://example.com).')
    assert "context manager" in masked
    assert "torch.mps.Stream" not in masked
    translated = masked.replace("Use ", "").replace(" and the ", " 및 ").replace(" context manager", " 컨텍스트 매니저")
    assert '[`torch.mps.Stream` 및 `torch.mps.stream` 컨텍스트 매니저](https://example.com)' in restore_inline(translated, saved)


def test_images_remain_opaque_even_inside_links():
    masked, saved = protect_inline('[![English alt](image.png)](https://example.com)')
    assert 'English alt' not in masked
    assert restore_inline(masked, saved) == '[![English alt](image.png)](https://example.com)'


def test_explicit_reference_labels_translate_and_implicit_references_stay_opaque():
    source = '[the guide][id] [id][] [id]\n\n[id]: /guide "Title"\n'
    masked, saved = protect_inline(source)
    assert 'the guide' in masked
    assert '[id]' not in masked
    assert restore_inline(masked.replace('the guide', '가이드'), saved) == source.replace('the guide', '가이드')


@pytest.mark.parametrize("change", [
    lambda s: s.replace('{{KEEP_0}}', ''),
    lambda s: s + '{{KEEP_0}}',
    lambda s: s + '{{KEEP_999}}',
])
def test_missing_duplicate_or_unknown_tokens_are_rejected(change):
    masked, saved = protect_inline('[guide](https://example.com)')
    with pytest.raises(ValueError, match='placeholder'):
        restore_inline(change(masked), saved)


def test_reserved_source_placeholder_is_rejected():
    with pytest.raises(ValueError, match='reserved'):
        protect_inline('Literal {{KEEP_0}} and [guide](https://example.com)')


def test_reference_definitions_survive_document_reconstruction():
    source = 'See [the guide][id].\n\n[id]: https://example.com "Guide"\n\nNext paragraph.\n'
    assert restore_body(parse_markdown_blocks(source), {}) == source


def test_pipeline_translates_link_labels_and_preserves_document_references(monkeypatch):
    monkeypatch.setattr('scripts.ecl_translation_pipeline.load_quality_glossaries', lambda: {})
    source = '# Guide\n\nSee [the guide][id] and [id].\n\n[id]: https://example.com "Title"\n\nRun `api()`.\n\n```python\nprint("unchanged")\n```\n'

    def model_call(prompt):
        items = json.loads(prompt.split('[Input JSON]\n', 1)[1])
        for item in items:
            item['markdown'] = item['markdown'].replace('the guide', '가이드').replace('See ', '참고: ')
        return json.dumps(items)

    result = translate_markdown_with_ecl(source, 'Translate into Korean.', 'Korean', model_call,
                                         use_external_glossary=False)
    assert '[가이드][id]' in result
    assert '[id]: https://example.com "Title"' in result
    assert '[id].' in result
    assert '`api()`' in result
    assert 'print("unchanged")' in result
    env = {}
    parsed = MarkdownIt().parse(result, env)
    hrefs = Counter(c.attrGet('href') for t in parsed for c in (t.children or []) if c.type == 'link_open')
    assert hrefs == Counter({'https://example.com': 2})


def test_pipeline_rejects_missing_link_target(monkeypatch):
    monkeypatch.setattr('scripts.ecl_translation_pipeline.load_quality_glossaries', lambda: {})

    def model_call(prompt):
        items = json.loads(prompt.split('[Input JSON]\n', 1)[1])
        items[0]['markdown'] = '문서만 남고 링크 목적지는 누락되었습니다.'
        return json.dumps(items)

    with pytest.raises(ValueError, match='placeholder'):
        translate_markdown_with_ecl('See [the guide](https://example.com).', '', 'Korean', model_call,
                                    use_external_glossary=False)
