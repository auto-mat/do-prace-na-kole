
from modeltranslation.admin import TranslationAdmin

from sitetree.admin import TreeItemAdmin, override_item_admin


class ModeltranslationTreeItemAdmin(TreeItemAdmin, TranslationAdmin):
    """This allows admin contrib to support translations for tree items."""


override_item_admin(ModeltranslationTreeItemAdmin)
