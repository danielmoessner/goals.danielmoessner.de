from typing import TYPE_CHECKING

from django.db import models

from apps.users.models import CustomUser


class Goal(models.Model):
    user = models.ForeignKey(CustomUser, related_name="goals", on_delete=models.CASCADE)
    name = models.CharField(max_length=300)
    why = models.TextField(blank=True, null=True)
    impact = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField(null=True, blank=True)
    sub_goals = models.ManyToManyField(
        to="self", through="Link", symmetrical=False, related_name="master_goals"
    )
    is_archived = models.BooleanField(default=False)
    addition = models.TextField(blank=True, null=True)
    progress = models.PositiveSmallIntegerField(default=0, blank=True)
    is_starred = models.BooleanField(default=False)
    created = models.DateTimeField(auto_created=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    if TYPE_CHECKING:
        master_goals: models.QuerySet["Goal"]
        sub_goals: models.ManyToManyField["Goal", "Goal"]
        progress_monitors: models.QuerySet["ProgressMonitor"]
        strategies: models.QuerySet["Strategy"]
        sub_links: models.QuerySet["Link"]
        master_links: models.QuerySet["Link"]

    class Meta:
        ordering = ("is_archived", "name")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for goal in list(self.master_goals.all()):
            goal.reset()

    def delete(self, *args, **kwargs):
        goals = list(self.master_goals.all())
        ret = super().delete(*args, **kwargs)
        for goal in goals:
            goal.reset()
        return ret

    @property
    def progress_str(self):
        return f"{self.progress}%"

    @staticmethod
    def get_goals(goals, include_archived_goals=False):
        if not include_archived_goals:
            goals = goals.filter(is_archived=False)
        return goals

    @staticmethod
    def get_goals_user(user, choice, include_archived_goals=False):
        goals = user.goals.all()
        goals = Goal.get_goals(goals, include_archived_goals)
        return goals

    def get_tree_subgoals(self, user):
        queryset = self.sub_goals.all()
        queryset = Goal.get_goals(
            queryset, include_archived_goals=user.show_archived_objects
        )
        return queryset

    def get_tree_monitors(self, user):
        queryset = self.progress_monitors.all()
        queryset = ProgressMonitor.get_monitors(
            queryset, included_archived_progress_monitors=user.show_archived_objects
        )
        return queryset

    def get_tree_strategies(self, user):
        queryset = self.strategies.all()
        queryset = Strategy.get_strategies(
            queryset, include_archived_strategies=user.show_archived_objects
        )
        return queryset

    def get_all_sub_goals(self):
        query: models.QuerySet[Goal] = self.sub_goals.all()
        for goal in self.sub_goals.all():
            query = query | goal.get_all_sub_goals()
        return query

    def get_all_sub_monitors(self):
        query = self.progress_monitors.all()
        for goal in self.get_all_sub_goals():
            query = query | goal.progress_monitors.all()
        return query

    def get_all_sub_strategies(self):
        query = self.strategies.all()
        for goal in self.get_all_sub_goals():
            query = query | goal.strategies.all()
        return query

    def get_all_sub_links(self):
        query = self.sub_links.all()
        for goal in self.get_all_sub_goals():
            query = query | goal.sub_links.all()
        return query

    def get_all_master_objects(self):
        objects = list()
        links = list(self.master_links.all())
        objects += links
        for link in links:
            objects += link.get_all_master_objects()
        return objects

    def get_all_mastergoals(self):
        query = self.master_goals.all()
        for goal in self.master_goals.all():
            query = query | goal.get_all_mastergoals()
        return query

    def get_progress_calc(self):
        progress = 0
        weight = 0

        for monitor in self.progress_monitors.all():
            progress += monitor.progress * monitor.weight
            weight += monitor.weight

        for link in self.sub_links.all():
            progress += link.progress * link.weight
            weight += link.weight

        if weight == 0:
            return 0

        return int(round(progress / weight))

    def reset(self):
        self.progress = self.get_progress_calc()
        self.save()


class ProgressMonitor(models.Model):
    goal = models.ForeignKey(
        Goal, on_delete=models.CASCADE, related_name="progress_monitors"
    )
    name = models.CharField(max_length=300)
    weight = models.PositiveSmallIntegerField(default=1)
    steps = models.PositiveSmallIntegerField()
    step = models.PositiveSmallIntegerField(default=0, blank=True)
    notes = models.TextField(default="", blank=True)
    is_archived = models.BooleanField(default=False)
    created = models.DateTimeField(auto_created=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    # general
    @property
    def progress(self):
        return (
            round((float(self.step) / float(self.steps)) * 100)
            if self.steps != 0
            else 100
        )

    @property
    def progress_str(self):
        return f"{self.progress}%"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.step > self.steps:
            self.step = self.steps
        if self.step < 0:
            self.step = 0
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        # calculate the goals progress
        self.goal.reset()

    class Meta:
        ordering = ("is_archived", "name", "goal")

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        goal = self.goal
        ret = super(ProgressMonitor, self).delete(
            using=using, keep_parents=keep_parents
        )
        goal.reset()
        return ret

    # getters
    @staticmethod
    def get_monitors(monitors, included_archived_progress_monitors=False):
        if not included_archived_progress_monitors:
            monitors = monitors.filter(is_archived=False)
        return monitors

    @staticmethod
    def get_monitors_user(user, included_archived_progress_monitors=False):
        goals = Goal.get_goals_user(
            user, "ALL", include_archived_goals=included_archived_progress_monitors
        )
        monitors = ProgressMonitor.objects.filter(goal__in=goals)
        monitors = ProgressMonitor.get_monitors(
            monitors, included_archived_progress_monitors
        )
        return monitors

    def get_all_master_objects(self):
        objects = list()
        objects += [self.goal]
        objects += self.goal.get_all_master_objects()
        return objects

    def get_notes(self):
        if self.notes:
            return self.notes
        return ""

    def get_tree(self):
        data = dict()
        data["name"] = self.name
        data["progress"] = self.progress
        data["pk"] = self.pk
        return data

    def increase_progress(self):
        self.step = min(self.step + 1, self.steps)

    def decrease_progress(self):
        self.step = max(self.step - 1, 0)


class Link(models.Model):
    master_goal = models.ForeignKey(
        Goal, on_delete=models.CASCADE, related_name="sub_links"
    )
    sub_goal = models.OneToOneField(
        Goal, on_delete=models.CASCADE, related_name="master_links"
    )
    weight = models.PositiveSmallIntegerField(default=1)
    is_archived = models.BooleanField(default=False)
    created = models.DateTimeField(auto_created=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    # general
    @property
    def progress(self):
        return self.sub_goal.progress

    class Meta:
        ordering = ("is_archived", "master_goal")

    def __str__(self):
        return self.get_name()

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        # reset the master goal progress
        self.master_goal.reset()

    def delete(self, using=None, keep_parents=False):
        master_goal = self.master_goal
        ret = super(Link, self).delete(using=using, keep_parents=keep_parents)
        master_goal.reset()
        return ret

    # getters
    @staticmethod
    def get_links(links, include_archived_links=False):
        if not include_archived_links:
            links.filter(is_archived=False)
        return links

    @staticmethod
    def get_links_user(user, include_archived_links=False):
        goals = Goal.get_goals_user(user, "ALL", include_archived_links)
        links = Link.objects.filter(master_goal__in=goals, sub_goal__in=goals)
        links = Link.get_links(links, include_archived_links)
        return links

    def get_all_master_objects(self):
        objects = list()
        objects += [self.master_goal]
        objects += self.master_goal.get_all_master_objects()
        return objects

    def get_all_sub_goals(self):
        query = Goal.objects.filter(pk=self.sub_goal.pk)
        query = query | self.sub_goal.get_all_sub_goals()
        return query

    def get_all_sub_strategies(self):
        return self.sub_goal.get_all_sub_strategies()

    def get_all_sub_links(self):
        return self.sub_goal.get_all_sub_links()

    def get_all_sub_monitors(self):
        return self.sub_goal.get_all_sub_monitors()

    def get_name(self):
        return self.master_goal.name + " --> " + self.sub_goal.name


class Strategy(models.Model):
    name = models.CharField(max_length=300)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="strategies")
    description = models.TextField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    created = models.DateTimeField(auto_created=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    # general
    class Meta:
        ordering = ("is_archived", "name")

    def __str__(self):
        return str(self.name)

    # getters
    @staticmethod
    def get_strategies(strategies, include_archived_strategies=False):
        if not include_archived_strategies:
            strategies = strategies.filter(is_archived=False)
        return strategies

    @staticmethod
    def get_strategies_goals(goals, include_archived_strategies=False):
        strategies = Strategy.objects.filter(goal__in=goals)

        strategies = Strategy.get_strategies(strategies, include_archived_strategies)

        return strategies

    @staticmethod
    def get_strategies_user(user, include_archived_strategies=False):
        goals = Goal.get_goals_user(
            user, "ALL", include_archived_goals=include_archived_strategies
        )
        strategies = Strategy.get_strategies_goals(goals, include_archived_strategies)
        return strategies

    def get_all_master_objects(self):
        objects = list()
        objects += [self.goal]
        objects += self.goal.get_all_master_objects()
        return objects
