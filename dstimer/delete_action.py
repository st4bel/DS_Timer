import os


def delete_single(id, folder="schedule"):
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", folder)
    trash_path = os.path.join(os.path.expanduser("~"), ".dstimer", "trash")
    for file in os.listdir(schedule_path):
        if id in file:
            os.rename(os.path.join(schedule_path, file), os.path.join(trash_path, file))
            return True


def delete_all():
    schedule_path = os.path.join(os.path.expanduser("~"), ".dstimer", "schedule")
    trash_path = os.path.join(os.path.expanduser("~"), ".dstimer", "trash")
    for file in os.listdir(schedule_path):
        os.rename(os.path.join(schedule_path, file), os.path.join(trash_path, file))
