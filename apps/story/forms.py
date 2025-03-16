from django import forms

from apps.story.models import Story
from config.form_class import FormClass
from config.mixins import OptsUserInstance


class UpdateStory(FormClass, OptsUserInstance[Story], forms.ModelForm):
    addons = {"navs": ["story"]}

    class Meta:
        model = Story
        fields = ["what_is", "what_should_be"]

    def init(self):
        latest = self.user.stories.first()
        if latest:
            self.fields["what_is"].initial = latest.what_is
            self.fields["what_should_be"].initial = latest.what_should_be

    def ok(self):
        self.instance.user = self.user
        self.instance.save()
        return self.instance.pk
