from django.db.models import Q
from django.db.models.functions import TruncDate

from ybooking.celery import app
from ybooking_app.models import Timetable, Profile, DayInterval, Vacation
from datetime import datetime, timedelta


@app.task
def generate_timeslots():
    """
    Create Timetable items for all doctors
    """
    today_day = datetime.today()

    doctors = Profile.objects.filter(
        user__is_active=True,
        is_doctor=True,
        schedule__isnull=False,
        schedule__planning_days__gt=0,
        schedule__session_duration__gt=0,
    )

    for doctor in doctors.iterator():
        # define days to generate schedule
        days_to_generate = [
            today_day + timedelta(days=i) for i in range(doctor.planning_days)
        ]
        days_range = (days_to_generate[0], days_to_generate[-1])

        # remove days for which timeslots has already been generated
        already_processed_days = Timetable.objects.filter(
            start__range=days_range,
            doctor_id=doctor.id,
        ).annotate(
            start_day=TruncDate('start'),
        ).values_list('start_day', flat=True).distinct()

        for day in already_processed_days:
            if day in days_to_generate:
                days_to_generate.remove(day)

        # remove intersection with vacations
        vacations = Vacation.objects.filter(
            Q(Q(start_date__range=days_range) | Q(stop_date__range=days_range)),
            doctor_id=doctor.id,
        )
        for vacation in vacations:
            for day in range(vacation.start_date, vacation.stop_date):
                if day in days_to_generate:
                    days_to_generate.remove(day)

        # define weekdays to generate schedule
        weekdays_to_generate = {day.weekday(): day for day in days_to_generate}

        # find all suitable time intervals
        intervals = DayInterval.objects.filter(
            doctor_id=doctor.id,
            weekday__in=weekdays_to_generate.keys(),
        )

        # generate timeslots for each interval
        sessions = []
        for interval in intervals:
            current_start_time = interval.start_time

            while current_start_time + doctor.session_duration <= interval.stop_time:

                sessions.append(Timetable(
                    doctor_id=doctor.id,
                    patient_id=None,
                    start=datetime.combine(
                        weekdays_to_generate[interval.weekday],
                        current_start_time,
                    ),
                    stop=datetime.combine(
                        weekdays_to_generate[interval.weekday],
                        current_start_time + doctor.session_duration,
                    ),
                ))

                current_start_time -= doctor.session_duration

        Timetable.objects.bulk_create(sessions)