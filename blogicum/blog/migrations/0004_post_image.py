from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(
                blank=True,
                upload_to='posts_images/',
                verbose_name='Изображение',
            ),
        ),
        migrations.AlterModelOptions(
            name='post',
            options={
                'ordering': ('-pub_date',),
                'verbose_name': 'публикация',
                'verbose_name_plural': 'Публикации',
            },
        ),
    ]
