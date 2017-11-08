import re
import pytz
from datetime import datetime
from backuper.utils.validate import validate_empty_snapshots
from backuper.utils.constants import timeMapper


class BackuperFilter(object):

    def regex_filter(self, filter, snapshots):

        filtered = []

        for i in snapshots:
            m = re.match(filter['pattern'], i['snapshotName'])
            if m:
                filtered.append(i)

        validate_empty_snapshots(filtered, 'Any matches by regex filter...')

        return filtered

    def age_filter(self, filter, snapshots):

        def check_age(s_date, unit, count):

            seconds = timeMapper[unit] * count
            today = datetime.utcnow().replace(tzinfo=pytz.utc)
            delta = today - s_date
            delta_time = delta.total_seconds()

            return delta_time > seconds

        filtered = [i for i in snapshots if check_age(i['creationTime'],
                                                      filter['unit'],
                                                      filter['count'])]

        validate_empty_snapshots(filtered, 'Any matches by age filter...')

        return filtered

    def filter_matcher(self, type):

        types = {'regex': self.regex_filter,
                 'age': self.age_filter}

        return types[type]


def main(filters, snapshots):

    snapshots = snapshots

    if filters is not None:
        for i in filters:
            f = getattr(BackuperFilter(), 'filter_matcher')(i['type'])
            snapshots = f(i, snapshots)

    return snapshots
