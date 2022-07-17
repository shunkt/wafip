import time
from math import exp


def exponential_backoff(retry_count: int):
    for n in range(retry_count):
        time.sleep(exp(n/2))
        yield
