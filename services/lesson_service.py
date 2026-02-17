def create_lesson(
    subject,
    topic,
    grade_level,
    objectives,
    duration,
    strategy,
    assessment
):
    """
    Creates a lesson dictionary.
    (Later: this will be saved to the database)
    """

    lesson = {
        "subject": subject,
        "topic": topic,
        "grade_level": grade_level,
        "objectives": objectives,
        "duration_minutes": duration,
        "strategy": strategy,
        "assessment": assessment
    }

    return lesson
