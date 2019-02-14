from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailmessage',
            name='sent',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
