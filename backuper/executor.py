import logging
import multiprocessing
import threading

from .params import AdapterParam, Bool, ParamsBase, Str, Int
from .pool import get_pool


logger = logging.getLogger(__name__)


_EXECUTOR_REGISTRY = {}


def build_executor_registry(executor, path=(0,)):
    global _EXECUTOR_REGISTRY
    _EXECUTOR_REGISTRY[path] = executor
    executor._reg_path = path
    if isinstance(executor, GroupExecutorBase):
        for idx, task in enumerate(executor.tasks):
            build_executor_registry(task, path=path + (idx,))


class Executor:

    timeout: Int = 0
    ignore_errors: Bool = False

    def __init__(self):
        super().__init__()

        self._done = multiprocessing.Event()
        self._result = None
        self._watchdog = threading.Thread(target=self._watch)
        self._terminating = False
        self._callback = None
        self._runner = None

        # TODO: move out
        self._reg_path = None

    def start(self, callback=None):
        logger.debug('START %s', self)
        assert self._runner is None
        self._callback = callback
        self._watchdog.start()

    def _watch(self):
        done = self._done.wait(self.timeout or None)  # TODO: Optional[Int]
        if not done:
            logger.warning('TIMEOUT %s', self)
            self._terminate()
            self._call_callback(None)
        else:
            logger.debug('DONE %s', self)
            self._call_callback(self._result)

    def _call_callback(self, value):
        if self._callback:
            self._callback(value)

    def _join(self):
        if self._runner:
            self._runner.join()
        self._watchdog.join()
        logger.debug('JOINED %s', self)

    def get_result(self):
        self._join()
        return self._result

    def __str__(self):
        return '-'.join(
            str(part) for part in
            (self.__class__.__name__,) + (self._reg_path or ())
        )

    def _terminate(self):
        raise NotImplementedError


class GroupExecutorBase(Executor):

    group: Str = ''
    parallel: Int = 1

    def __init__(self):
        super().__init__()

        self.description = self.group.strip()
        self.tasks = None

        self._sem = threading.Semaphore(self.parallel)

        self._result_lock = threading.Lock()

    def start(self, callback=None):
        assert self.tasks is not None
        super().start(callback=callback)
        name = 'GroupThread-' + '-'.join(str(p) for p in self._reg_path)
        self._runner = threading.Thread(target=self._run, name=name)
        self._runner.start()

    def _run(self):
        logger.debug('GROUP THREAD START %s', self)
        try:
            self._result = []
            for task in self.tasks:
                self._sem.acquire()
                with self._result_lock:
                    if self._terminating:
                        break
                    task.start(callback=self._on_task_done)
                    self._result.append(task)
            self._result = [task.get_result() for task in self._result]
        finally:
            self._done.set()

    def _on_task_done(self, result):
        self._sem.release()

    def _terminate(self):
        if not self._terminating:
            with self._result_lock:
                self._terminating = True
                self._sem.release()
                for task in self._result:
                    task._terminate()


class GroupExecutor(ParamsBase, GroupExecutorBase):
    pass


class AdapterExecutorBase(Executor):

    action: AdapterParam

    def __init__(self):
        super().__init__()

        self.adapter = None

        self._proc_queue = multiprocessing.SimpleQueue()
        self._proc_queue_lock = multiprocessing.Lock()

        self._description = self.action.description

    def init_adapter(self, **params):
        self.adapter = self.action.cls(**params)

    def start(self, callback=None):
        super().start(callback=callback)
        assert self._result is None
        self._result = get_pool().apply_async(_run_adapter, (self._reg_path,))

    def _run(self):
        try:
            return self.adapter.run()
        finally:
            self._done.set()

    def _join(self):
        self._get_runner()
        super()._join()
        if self._result.ready():
            self._result = self._result.get()

    def _terminate(self):
        if not self._terminating:
            self._terminating = True
            self._get_runner()
            if self._runner:
                self._runner.terminate()

    def _get_runner(self):
        if not self._runner:
            process_id = None
            with self._proc_queue_lock:
                if not self._proc_queue.empty():
                    process_id = self._proc_queue.get()
                    if process_id is None:
                        self._proc_queue.put(None)
                elif self._terminating:
                    self._proc_queue.put(None)
            if process_id:
                logger.debug('GOT RUNNER %s %s', process_id, self)
                self._runner = get_pool().get_process_by_id(process_id)


class AdapterExecutor(ParamsBase, AdapterExecutorBase):
    pass


def _run_adapter(reg_path):
    executor = _EXECUTOR_REGISTRY[reg_path]
    with executor._proc_queue_lock:
        if not executor._proc_queue.empty():
            return
        process = multiprocessing.current_process()
        executor._proc_queue.put(process._identity)
    logger.debug(
        'ADAPTER TASK START %s %s', process._identity, executor.adapter)
    return executor._run()
