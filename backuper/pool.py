import logging

from multiprocessing import log_to_stderr, pool


logger = logging.getLogger(__name__)


class BasePool(pool.Pool):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._worker_handler.name = 'WorkerHandler'
        self._task_handler.name = 'TaskHandler'
        self._result_handler.name = 'ResultHandler'

    def get_process_by_id(self, process_id):
        for process in self._pool:
            if process._identity == process_id:
                return process


class ScalingPool(BasePool):

    def __init__(self, *args, max_processes=100, **kwargs):
        self.max_processes = max_processes
        self.tasks_in = self.tasks_out = 0
        super().__init__(*args, maxtasksperchild=1, **kwargs)

    def _setup_queues(self):
        super()._setup_queues()
        _quick_put = self._quick_put
        _quick_get = self._quick_get

        def counting_put(obj):
            logger.debug('POOL PUT %s', obj)
            _quick_put(obj)
            if obj is not None:
                self.tasks_in += 1

        def counting_get():
            obj = _quick_get()
            logger.debug('POOL GET %s', obj)
            if obj is not None:
                self.tasks_out += 1
            return obj

        self._quick_put = counting_put
        self._quick_get = counting_get

    def _maintain_pool(self):
        _proc_save = self._processes
        num_waiting_tasks = self.tasks_in - self.tasks_out
        self._processes = max(1, min(num_waiting_tasks, self.max_processes))
        if _proc_save != self._processes:
            logger.debug('SCALE %s -> %s', _proc_save,  self._processes)
        self._repopulate_pool()
        self._join_exited_workers()


_POOL = None


def get_pool(*args, log_level=None, **kwargs):
    global _POOL
    if _POOL is None:
        if log_level is not None:
            log_to_stderr(log_level)
        _POOL = ScalingPool(*args, processes=1, **kwargs)
    return _POOL
