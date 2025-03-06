from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AccountModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('minimum_balance', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('maximum_balance', models.DecimalField(decimal_places=2, default=1000000000, max_digits=10)),
            ],
            options={
                'db_table': 'account',
            },
        ),
        migrations.CreateModel(
            name='TransactionModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(max_length=20)),
                ('source_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_transactions', to='accounts.accountmodel')),
                ('target_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_transactions', to='accounts.accountmodel')),
            ],
            options={
                'db_table': 'transaction',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='DailyLimitModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('used_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('reset_time', models.DateTimeField()),
                ('account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='daily_limit', to='accounts.accountmodel')),
            ],
            options={
                'db_table': 'daily_limit',
            },
        ),
        migrations.CreateModel(
            name='ActivityModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('owner_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_activities', to='accounts.accountmodel')),
                ('source_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_activities', to='accounts.accountmodel')),
                ('target_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_activities', to='accounts.accountmodel')),
            ],
            options={
                'db_table': 'activity',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='AccountStatementModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('opening_balance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('closing_balance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statements', to='accounts.accountmodel')),
            ],
            options={
                'db_table': 'account_statement',
                'ordering': ['-end_date'],
            },
        ),
    ] 