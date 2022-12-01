from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': "Текст поста",
            'group': "Группа",
            'image': "Картинка",
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError('Пост не может быть пустым.'
                                        'Поле обязательно для заполнения.')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        labels = {'text': "Текст комментария"}
        fields = ('text',)
