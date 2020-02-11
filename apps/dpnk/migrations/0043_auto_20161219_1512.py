# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0042_auto_20161129_1854'),
    ]

    database_operations = [
        migrations.AlterModelTable('DiscountCoupon', 'coupons_discountcoupon'),
        migrations.AlterModelTable('DiscountCouponType', 'coupons_discountcoupontype')
    ]

    state_operations = [
        migrations.DeleteModel('DiscountCoupon'),
        migrations.DeleteModel('DiscountCouponType')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]
