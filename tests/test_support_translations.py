import gettext
import inspect
import io
import os
import shutil
import struct
import tempfile

import pytest

from babel import support
from babel.messages import Catalog
from babel.messages.mofile import write_mo

messages1 = [
    ('foo', {'string': 'Voh'}),
    ('foo', {'string': 'VohCTX', 'context': 'foo'}),
    (('foo1', 'foos1'), {'string': ('Voh1', 'Vohs1')}),
    (('foo1', 'foos1'), {'string': ('VohCTX1', 'VohsCTX1'), 'context': 'foo'}),
]

messages2 = [
    ('foo', {'string': 'VohD'}),
    ('foo', {'string': 'VohCTXD', 'context': 'foo'}),
    (('foo1', 'foos1'), {'string': ('VohD1', 'VohsD1')}),
    (('foo1', 'foos1'), {'string': ('VohCTXD1', 'VohsCTXD1'), 'context': 'foo'}),
]


@pytest.fixture(autouse=True)
def use_en_us_locale(monkeypatch):
    # Use a locale which won't fail to run the tests
    monkeypatch.setenv('LANG', 'en_US.UTF-8')


@pytest.fixture
def translations() -> support.Translations:
    catalog1 = Catalog(locale='en_GB', domain='messages')
    catalog2 = Catalog(locale='en_GB', domain='messages1')
    for ids, kwargs in messages1:
        catalog1.add(ids, **kwargs)
    for ids, kwargs in messages2:
        catalog2.add(ids, **kwargs)
    catalog1_fp = io.BytesIO()
    catalog2_fp = io.BytesIO()
    write_mo(catalog1_fp, catalog1)
    catalog1_fp.seek(0)
    write_mo(catalog2_fp, catalog2)
    catalog2_fp.seek(0)
    translations1 = support.Translations(catalog1_fp)
    translations2 = support.Translations(catalog2_fp, domain='messages1')
    return translations1.add(translations2, merge=False)


@pytest.fixture(scope='module')
def empty_translations() -> support.Translations:
    fp = io.BytesIO()
    write_mo(fp, Catalog(locale='de'))
    fp.seek(0)
    return support.Translations(fp=fp)


@pytest.fixture(scope='module')
def null_translations() -> support.NullTranslations:
    fp = io.BytesIO()
    write_mo(fp, Catalog(locale='de'))
    fp.seek(0)
    return support.NullTranslations(fp=fp)


def assert_equal_type_too(expected, result) -> None:
    assert expected == result
    assert type(expected) is type(result), (
        f'instance types do not match: {type(expected)!r}!={type(result)!r}'
    )


def test_pgettext(translations):
    assert_equal_type_too('Voh', translations.gettext('foo'))
    assert_equal_type_too('VohCTX', translations.pgettext('foo', 'foo'))
    assert_equal_type_too('VohCTX1', translations.pgettext('foo', 'foo1'))


def test_pgettext_fallback(translations):
    fallback = translations._fallback
    translations._fallback = support.NullTranslations()
    assert translations.pgettext('foo', 'bar') == 'bar'
    translations._fallback = fallback


def test_upgettext(translations):
    assert_equal_type_too('Voh', translations.ugettext('foo'))
    assert_equal_type_too('VohCTX', translations.upgettext('foo', 'foo'))


def test_npgettext(translations):
    assert_equal_type_too('Voh1', translations.ngettext('foo1', 'foos1', 1))
    assert_equal_type_too('Vohs1', translations.ngettext('foo1', 'foos1', 2))
    assert_equal_type_too('VohCTX1', translations.npgettext('foo', 'foo1', 'foos1', 1))
    assert_equal_type_too('VohsCTX1', translations.npgettext('foo', 'foo1', 'foos1', 2))


def test_unpgettext(translations):
    assert_equal_type_too('Voh1', translations.ungettext('foo1', 'foos1', 1))
    assert_equal_type_too('Vohs1', translations.ungettext('foo1', 'foos1', 2))
    assert_equal_type_too('VohCTX1', translations.unpgettext('foo', 'foo1', 'foos1', 1))
    assert_equal_type_too('VohsCTX1', translations.unpgettext('foo', 'foo1', 'foos1', 2))


def test_dpgettext(translations):
    assert_equal_type_too('VohD', translations.dgettext('messages1', 'foo'))
    assert_equal_type_too('VohCTXD', translations.dpgettext('messages1', 'foo', 'foo'))


def test_dupgettext(translations):
    assert_equal_type_too('VohD', translations.dugettext('messages1', 'foo'))
    assert_equal_type_too('VohCTXD', translations.dupgettext('messages1', 'foo', 'foo'))


def test_dnpgettext(translations):
    assert_equal_type_too('VohD1', translations.dngettext('messages1', 'foo1', 'foos1', 1))
    assert_equal_type_too('VohsD1', translations.dngettext('messages1', 'foo1', 'foos1', 2))
    assert_equal_type_too('VohCTXD1', translations.dnpgettext('messages1', 'foo', 'foo1', 'foos1', 1))
    assert_equal_type_too('VohsCTXD1', translations.dnpgettext('messages1', 'foo', 'foo1', 'foos1', 2))


def test_dunpgettext(translations):
    assert_equal_type_too('VohD1', translations.dungettext('messages1', 'foo1', 'foos1', 1))
    assert_equal_type_too('VohsD1', translations.dungettext('messages1', 'foo1', 'foos1', 2))
    assert_equal_type_too('VohCTXD1', translations.dunpgettext('messages1', 'foo', 'foo1', 'foos1', 1))
    assert_equal_type_too('VohsCTXD1', translations.dunpgettext('messages1', 'foo', 'foo1', 'foos1', 2))


def test_load(translations):
    tempdir = tempfile.mkdtemp()
    try:
        messages_dir = os.path.join(tempdir, 'fr', 'LC_MESSAGES')
        os.makedirs(messages_dir)
        catalog = Catalog(locale='fr', domain='messages')
        catalog.add('foo', 'bar')
        with open(os.path.join(messages_dir, 'messages.mo'), 'wb') as f:
            write_mo(f, catalog)

        translations = support.Translations.load(tempdir, locales=('fr',), domain='messages')
        assert translations.gettext('foo') == 'bar'
    finally:
        shutil.rmtree(tempdir)


def get_gettext_method_names(obj):
    # Deprecated l*gettext functions are not included
    return [name for name in dir(obj) if 'gettext' in name and not name.startswith('l')]


def test_null_translations_have_same_methods(empty_translations, null_translations):
    for name in get_gettext_method_names(empty_translations):
        assert hasattr(null_translations, name), (
            f'NullTranslations does not provide method {name!r}'
        )


def test_null_translations_method_signature_compatibility(
    empty_translations,
    null_translations,
):
    for name in get_gettext_method_names(empty_translations):
        spec1 = inspect.getfullargspec(getattr(empty_translations, name))
        spec2 = inspect.getfullargspec(getattr(null_translations, name))
        assert spec1 == spec2


def test_null_translations_same_return_values(empty_translations, null_translations):
    data = {
        'message': 'foo',
        'domain': 'domain',
        'context': 'tests',
        'singular': 'bar',
        'plural': 'baz',
        'num': 1,
        'msgid1': 'bar',
        'msgid2': 'baz',
        'n': 1,
    }
    for name in get_gettext_method_names(empty_translations):
        method = getattr(empty_translations, name)
        null_method = getattr(null_translations, name)
        signature = inspect.getfullargspec(method)
        parameter_names = [name for name in signature.args if name != 'self']
        values = [data[name] for name in parameter_names]
        assert method(*values) == null_method(*values)


def test_catalog_merge_files():
    # Refs issues #92, #162
    t1 = support.Translations()
    assert t1.files == []
    t1._catalog['foo'] = 'bar'
    fp = io.BytesIO()
    write_mo(fp, Catalog())
    fp.seek(0)
    fp.name = 'pro.mo'
    t2 = support.Translations(fp)
    assert t2.files == ['pro.mo']
    t2._catalog['bar'] = 'quux'
    t1.merge(t2)
    assert t1.files == ['pro.mo']
    assert set(t1._catalog.keys()) == {'', 'foo', 'bar'}



@pytest.fixture
def make_plural_translations():
    def make(locale, cls=support.Translations, domain=None, translated=True, charset='utf-8'):
        forms = {
            'en': ('one', 'other'),
            'ja': ('all',),
            'ru': ('one', 'few', 'many'),
        }[locale]
        catalog = Catalog(locale=locale, charset=charset)
        if translated:
            catalog.add(('item', 'items'), forms)
        stream = io.BytesIO()
        stream.name = 'incoming.mo'
        write_mo(stream, catalog)
        stream.seek(0)
        if cls is support.Translations:
            return cls(stream, domain=domain)
        return cls(stream)
    return make


@pytest.mark.parametrize('locale', ['ru', 'ja', 'en'])
@pytest.mark.parametrize('source_class', [support.Translations, gettext.GNUTranslations])
@pytest.mark.parametrize('method', ['merge', 'add'])
def test_empty_merge_initializes_catalog_metadata(make_plural_translations, locale, source_class, method):
    source = make_plural_translations(locale, cls=source_class)
    target = support.Translations()
    assert getattr(target, method)(source) is target
    for count in [0, 1, 2, 5, 11, 21, 22, 25]:
        assert target.ngettext('item', 'items', count) == source.ngettext('item', 'items', count)
    assert target.info() == source.info()
    assert target.info() is not source.info()
    assert target.charset() == source.charset()
    assert target.domain == support.Translations.DEFAULT_DOMAIN


@pytest.mark.parametrize('state', ['message', 'header', 'info', 'charset', 'custom_plural'])
def test_merge_retains_initialized_receiver_metadata(make_plural_translations, state):
    source = make_plural_translations('ru')
    target = support.Translations()
    if state == 'message':
        target._catalog['old'] = 'old translation'
    elif state == 'header':
        target = make_plural_translations('en', translated=False)
    elif state == 'info':
        target._info['project-id-version'] = 'existing'
    elif state == 'charset':
        target._charset = 'iso-8859-1'
    elif state == 'custom_plural':
        target.plural = lambda num: 0
    old_plural, old_info, old_charset = target.plural, target.info().copy(), target.charset()
    target.merge(source)
    assert target.plural is old_plural
    assert target.info() == old_info
    assert target.charset() == old_charset


def test_empty_merge_metadata_is_independent(make_plural_translations):
    source = make_plural_translations('ru', charset='iso-8859-1')
    target = support.Translations()
    target.merge(source)
    assert target.charset() == 'iso-8859-1'
    source.info()['source-only'] = 'value'
    target.info()['target-only'] = 'value'
    assert 'source-only' not in target.info()
    assert 'target-only' not in source.info()


def test_empty_merge_preserves_domain_files_and_fallback(make_plural_translations):
    source = make_plural_translations('ru', domain='plugin')
    source.add_fallback(support.NullTranslations())
    target = support.Translations(domain='application')
    fallback = support.NullTranslations()
    target.add_fallback(fallback)
    target.merge(source)
    assert target.domain == 'application'
    assert target.files == ['incoming.mo']
    assert target._fallback is fallback
    assert target._fallback is not source._fallback


def test_other_domain_add_does_not_initialize_main_metadata(make_plural_translations):
    source = make_plural_translations('ru', domain='plugin')
    target = support.Translations()
    old_plural = target.plural
    target.add(source)
    assert target.plural is old_plural
    assert target.info() == {}
    assert target.charset() is None
    assert target.files == []
    assert target.dngettext('plugin', 'item', 'items', 5) == 'many'
    assert target.ngettext('item', 'items', 5) == 'items'


def test_empty_same_domain_add_initializes_metadata(make_plural_translations):
    source = make_plural_translations('ru', domain='plugin')
    target = support.Translations(domain='plugin')
    target.add(source)
    assert target.ngettext('item', 'items', 5) == 'many'
    assert target.domain == 'plugin'


def test_merging_empty_catalog_keeps_receiver_uninitialized(make_plural_translations):
    target = support.Translations()
    target.merge(support.Translations())
    source = make_plural_translations('ru')
    target.merge(source)
    assert target.ngettext('item', 'items', 5) == 'many'
    assert target.info() == source.info()


def test_first_header_only_merge_initializes_receiver_once(make_plural_translations):
    target = support.Translations()
    first = make_plural_translations('en', translated=False)
    target.merge(first)
    assert target.plural is first.plural
    assert target.info() == first.info()
    old_plural, old_info = target.plural, target.info().copy()
    target.merge(make_plural_translations('ru'))
    assert target.plural is old_plural
    assert target.info() == old_info
    assert target.ngettext('item', 'items', 5) == 'few'


@pytest.mark.parametrize('source_class', [support.Translations, gettext.GNUTranslations])
@pytest.mark.parametrize('custom_plural', [False, True])
def test_merging_zero_entry_mo_keeps_receiver_uninitialized(make_plural_translations, source_class, custom_plural):
    # A valid MO with no header or messages still installs GNU's own plural rule.
    source = source_class(io.BytesIO(struct.pack('<7I', 0x950412de, 0, 0, 28, 28, 0, 0)))
    if custom_plural:
        source.plural = lambda n: 0
    target = support.Translations()
    original_plural = target.plural
    target.merge(source)
    assert target.plural is original_plural
    assert target.info() == {}
    source = make_plural_translations('ru')
    target.merge(source)
    assert target.ngettext('item', 'items', 5) == 'many'
    assert target.info() == source.info()


def test_loaded_zero_entry_receiver_retains_its_rule(make_plural_translations):
    target = support.Translations(io.BytesIO(struct.pack('<7I', 0x950412de, 0, 0, 28, 28, 0, 0)))
    original_plural = target.plural
    target.merge(make_plural_translations('ru'))
    assert target.plural is original_plural
    assert target.info() == {}
    assert target.ngettext('item', 'items', 5) == 'few'


def test_default_plural_keeps_keyword_parameter_name():
    assert support.NullTranslations().plural(n=2) == 1
