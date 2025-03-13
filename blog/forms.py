from django import forms

from blog.models import Blog
from users.forms import MixinForms


class BlogCreationForm(MixinForms, forms.ModelForm):
    """ Форма создания и редактирования блога """

    class Meta:
        model = Blog
        fields = (
            "title",
            "topic",
            "is_published",
            "blog_text",
            "image",
        )

    def __init__(self, *args, **kwargs):
        """ Изменение формы чекбокса """
        super().__init__(*args, **kwargs)
        self.fields['is_published'].widget.attrs.update({
            'class': 'form-check-label',
        })
