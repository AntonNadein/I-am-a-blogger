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
            "blog_text",
            "image",
        )
