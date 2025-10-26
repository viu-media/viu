"""
Concurrency utilities for managing background tasks and thread lifecycle.

This module provides abstract base classes and concrete implementations for managing
background workers with proper lifecycle control, cancellation support, and resource cleanup.
"""

import logging
import threading
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar
from weakref import WeakSet

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Cancellable(Protocol):
    """Protocol for objects that can be cancelled."""

    def cancel(self) -> bool:
        """Cancel the operation. Returns True if cancellation was successful."""
        ...

    def cancelled(self) -> bool:
        """Return True if the operation was cancelled."""
        ...


class WorkerTask:
    """Represents a single task that can be executed by a worker."""

    def __init__(self, func: Callable[..., Any], *args, **kwargs):
        """
        Initialize a worker task.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._cancelled = threading.Event()
        self._completed = threading.Event()
        self._exception: Optional[Exception] = None
        self._result: Any = None

    def execute(self) -> Any:
        """Execute the task if not cancelled."""
        if self._cancelled.is_set():
            return None

        try:
            self._result = self.func(*self.args, **self.kwargs)
            return self._result
        except Exception as e:
            self._exception = e
            logger.error(f"Task execution failed: {e}")
            raise
        finally:
            self._completed.set()

    def cancel(self) -> bool:
        """Cancel the task."""
        if self._completed.is_set():
            return False
        self._cancelled.set()
        return True

    def cancelled(self) -> bool:
        """Check if the task was cancelled."""
        return self._cancelled.is_set()

    def completed(self) -> bool:
        """Check if the task completed."""
        return self._completed.is_set()

    @property
    def exception(self) -> Optional[Exception]:
        """Get the exception if one occurred during execution."""
        return self._exception

    @property
    def result(self) -> Any:
        """Get the result of the task execution."""
        return self._result


class BackgroundWorker(ABC):
    """
    Abstract base class for background workers that manage concurrent tasks.

    Provides lifecycle management, cancellation support, and proper resource cleanup.
    """

    def __init__(self, max_workers: int = 5, name: Optional[str] = None):
        """
        Initialize the background worker.

        Args:
            max_workers: Maximum number of concurrent worker threads
            name: Optional name for the worker (used in logging)
        """
        self.max_workers = max_workers
        self.name = name or self.__class__.__name__
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: WeakSet[Future] = WeakSet()
        self._tasks: List[WorkerTask] = []
        self._shutdown_event = threading.Event()
        self._lock = threading.RLock()
        self._started = False

    def start(self) -> None:
        """Start the background worker."""
        with self._lock:
            if self._started:
                logger.warning(f"Worker {self.name} is already started")
                return

            self._executor = ThreadPoolExecutor(
                max_workers=self.max_workers, thread_name_prefix=f"{self.name}-worker"
            )
            self._started = True
            logger.debug(f"Started background worker: {self.name}")

    def submit_task(self, task: WorkerTask) -> Future:
        """
        Submit a task for background execution.

        Args:
            task: The task to execute

        Returns:
            Future representing the task execution

        Raises:
            RuntimeError: If the worker is not started or is shutting down
        """
        with self._lock:
            if not self._started or self._shutdown_event.is_set():
                raise RuntimeError(f"Worker {self.name} is not available")

            if self._executor is None:
                raise RuntimeError(f"Worker {self.name} executor is not initialized")

            self._tasks.append(task)
            future = self._executor.submit(task.execute)
            self._futures.add(future)

            logger.debug(f"Submitted task to worker {self.name}")
            return future

    def submit_function(self, func: Callable[..., Any], *args, **kwargs) -> Future:
        """
        Submit a function for background execution.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Future representing the task execution
        """
        task = WorkerTask(func, *args, **kwargs)
        return self.submit_task(task)

    def cancel_all_tasks(self) -> int:
        """
        Cancel all pending and running tasks.

        Returns:
            Number of tasks that were successfully cancelled
        """
        cancelled_count = 0

        with self._lock:
            # Cancel all tasks
            for task in self._tasks:
                if task.cancel():
                    cancelled_count += 1

            # Cancel all futures
            for future in list(self._futures):
                if future.cancel():
                    cancelled_count += 1

        logger.debug(f"Cancelled {cancelled_count} tasks in worker {self.name}")
        return cancelled_count

    def shutdown(self, wait: bool = True, timeout: Optional[float] = 30.0) -> None:
        """
        Shutdown the background worker.

        Args:
            wait: Whether to wait for running tasks to complete
            timeout: Maximum time to wait for shutdown (ignored if wait=False)
        """
        with self._lock:
            if not self._started:
                return

            self._shutdown_event.set()
            self._started = False

            if self._executor is None:
                return

            logger.debug(f"Shutting down worker {self.name}")

            if not wait:
                # Cancel all tasks and shutdown immediately
                self.cancel_all_tasks()
                self._executor.shutdown(wait=False, cancel_futures=True)
            else:
                # Wait for tasks to complete with timeout
                try:
                    self._executor.shutdown(wait=True)
                except TimeoutError:
                    logger.warning(
                        f"Worker {self.name} shutdown timed out, forcing cancellation"
                    )
                    self.cancel_all_tasks()
                    self._executor.shutdown(wait=False, cancel_futures=True)

            self._executor = None
            logger.debug(f"Worker {self.name} shutdown complete")

    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self._started and not self._shutdown_event.is_set()

    def get_active_task_count(self) -> int:
        """Get the number of active (non-completed) tasks."""
        with self._lock:
            return sum(1 for task in self._tasks if not task.completed())

    @abstractmethod
    def _on_task_completed(self, task: WorkerTask, future: Future) -> None:
        """
        Hook called when a task completes (successfully or with error).

        Args:
            task: The completed task
            future: The future representing the task execution
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.shutdown(wait=True)


class ManagedBackgroundWorker(BackgroundWorker):
    """
    Concrete implementation of BackgroundWorker with task completion tracking.

    This worker provides additional monitoring and logging of task completion.
    """

    def __init__(self, max_workers: int = 5, name: Optional[str] = None):
        super().__init__(max_workers, name)
        self._completed_tasks: List[WorkerTask] = []
        self._failed_tasks: List[WorkerTask] = []

    def _on_task_completed(self, task: WorkerTask, future: Future) -> None:
        """Track completed tasks and log results."""
        try:
            if future.exception():
                self._failed_tasks.append(task)
                logger.error(f"Task failed in worker {self.name}: {future.exception()}")
            else:
                self._completed_tasks.append(task)
                logger.debug(f"Task completed successfully in worker {self.name}")
        except Exception as e:
            logger.error(f"Error in task completion handler: {e}")

    def get_completion_stats(self) -> Dict[str, int]:
        """Get statistics about task completion."""
        with self._lock:
            return {
                "total_tasks": len(self._tasks),
                "completed_tasks": len(self._completed_tasks),
                "failed_tasks": len(self._failed_tasks),
                "active_tasks": self.get_active_task_count(),
            }


class ThreadManager:
    """
    Manages multiple background workers and provides centralized control.

    This class acts as a registry for all background workers in the application,
    allowing for coordinated shutdown and monitoring.
    """

    def __init__(self):
        self._workers: Dict[str, BackgroundWorker] = {}
        self._lock = threading.RLock()

    def register_worker(self, name: str, worker: BackgroundWorker) -> None:
        """
        Register a background worker.

        Args:
            name: Unique name for the worker
            worker: The worker instance to register
        """
        with self._lock:
            if name in self._workers:
                raise ValueError(f"Worker with name '{name}' already registered")
            self._workers[name] = worker
            logger.debug(f"Registered worker: {name}")

    def get_worker(self, name: str) -> Optional[BackgroundWorker]:
        """Get a registered worker by name."""
        with self._lock:
            return self._workers.get(name)

    def shutdown_worker(
        self, name: str, wait: bool = True, timeout: Optional[float] = 30.0
    ) -> bool:
        """
        Shutdown a specific worker.

        Args:
            name: Name of the worker to shutdown
            wait: Whether to wait for completion
            timeout: Shutdown timeout

        Returns:
            True if worker was found and shutdown, False otherwise
        """
        with self._lock:
            worker = self._workers.get(name)
            if worker:
                worker.shutdown(wait=wait, timeout=timeout)
                del self._workers[name]
                logger.debug(f"Shutdown worker: {name}")
                return True
            return False

    def shutdown_all(self, wait: bool = True, timeout: Optional[float] = 30.0) -> None:
        """Shutdown all registered workers."""
        with self._lock:
            workers_to_shutdown = list(self._workers.items())

        for name, worker in workers_to_shutdown:
            try:
                worker.shutdown(wait=wait, timeout=timeout)
                logger.debug(f"Shutdown worker: {name}")
            except Exception as e:
                logger.error(f"Error shutting down worker {name}: {e}")

        with self._lock:
            self._workers.clear()

    def get_all_workers(self) -> Dict[str, BackgroundWorker]:
        """Get a copy of all registered workers."""
        with self._lock:
            return self._workers.copy()

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all workers."""
        status = {}
        with self._lock:
            for name, worker in self._workers.items():
                status[name] = {
                    "running": worker.is_running(),
                    "active_tasks": worker.get_active_task_count(),
                }

                if isinstance(worker, ManagedBackgroundWorker):
                    status[name].update(worker.get_completion_stats())

        return status


# Global thread manager instance
thread_manager = ThreadManager()
