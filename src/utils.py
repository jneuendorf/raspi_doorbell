def is_time_between(begin_time, end_time, check_time):
    """
    https://stackoverflow.com/a/10048290/6928824
    """
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    # crosses middo_not_disturb
    else:
        return check_time >= begin_time or check_time <= end_time
