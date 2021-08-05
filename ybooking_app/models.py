from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL, CASCADE
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    patronymic = models.CharField(max_length=150, blank=True, verbose_name='Patronymic (optional)')
    birthday = models.DateField(verbose_name='Birthday')
    is_doctor = models.BooleanField(default=False, verbose_name='Is doctor')

    Sex = models.IntegerChoices('Sex', 'MAN WOMAN UNDEFINED')
    sex = models.IntegerField(choices=Sex.choices, default=Sex.UNDEFINED, verbose_name='Sex')

    class Meta:
        db_table = 'profile'

    @property
    def is_patient(self):
        return not self.is_doctor


class Timetable(models.Model):
    doctor = models.ForeignKey(Profile, on_delete=CASCADE, verbose_name='Doctor', related_name='doctor')
    patient = models.ForeignKey(Profile, null=True, blank=True, on_delete=SET_NULL, verbose_name='Client')
    start = models.DateTimeField(verbose_name='Session start datetime')
    stop = models.DateTimeField(verbose_name='Session stop datetime')

    class Meta:
        db_table = 'timetable'


class Schedule(models.Model):
    doctor = models.ForeignKey(Profile, on_delete=CASCADE, verbose_name='Doctor')
    planning_days = models.IntegerField(default=7, verbose_name='Days number to generate sessions')
    session_duration = models.IntegerField(verbose_name='Session duration (min)')

    class Meta:
        db_table = 'schedule'


class DayInterval(models.Model):
    doctor = models.ForeignKey(Profile, on_delete=CASCADE, verbose_name='Doctor')
    start_time = models.TimeField(verbose_name='Interval start time')
    stop_time = models.TimeField(verbose_name='Interval stop time')

    Weekdays = models.IntegerChoices('Weekdays', 'MON TUE WED THU FRI SUN SAT')
    weekday = models.IntegerField(choices=Weekdays.choices, default=Weekdays.MON, verbose_name='Day of week')

    class Meta:
        db_table = 'interval'


class Vacation(models.Model):
    doctor = models.ForeignKey(Profile, on_delete=CASCADE, verbose_name='Doctor')
    start_date = models.DateField(verbose_name='Vacation start date')
    stop_date = models.DateField(verbose_name='Vacation stop date')

    class Meta:
        db_table = 'vacation'