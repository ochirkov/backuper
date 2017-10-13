import re
import pytz
from datetime import datetime
from .exceptions import BackuperNoSnapshotMatchError


def check_snapshot_match(snapshots, msg):

    if not snapshots:
        raise BackuperNoSnapshotMatchError(msg)


class BackuperFilter(object):

    def regex_filter(self, pattern, snapshots):

        filtered = []

        for i in snapshots:
            m = re.match(pattern, i['name'])

        if m:
            filtered.append(i)

        check_snapshot_match(filtered, 'Any matches by regex filter...')

        return filtered

    def age_filter(self, filter, snapshots):

        def check_days(s_date, days):

            today = datetime.utcnow().replace(tzinfo=pytz.utc)
            delta = today - s_date
            delta_days = delta.days

            return delta_days > days

        filtered = [i for i in snapshots if check_days(i['creation_time'], filter['count'])]


        check_snapshot_match(filtered, 'Any matches by age filter...')

        return filtered

    def filter_matcher(self, type):

        types = {'regex': self.regex_filter,
                 'age': self.age_filter}

        return types[type]


def main(filters, snapshots):

    for i in filters:
        f = getattr(BackuperFilter(), 'filter_matcher')(i['type'])
        result = f(i, snapshots)

    return result