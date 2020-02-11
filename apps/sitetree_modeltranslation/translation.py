from modeltranslation.translator import TranslationOptions, translator

from .models import ModeltranslationTreeItem


class TreeItemTranslationOptions(TranslationOptions):
    # These fields are for translation.
    fields = ('title', 'hint', 'description', 'url')


translator.register(ModeltranslationTreeItem, TreeItemTranslationOptions)
