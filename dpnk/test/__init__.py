from model_mommy import mommy

mommy.generators.add('smart_selects.db_fields.ChainedForeignKey', 'model_mommy.random_gen.gen_related')
