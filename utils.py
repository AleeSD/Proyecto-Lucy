import os
import sys
from contextlib import contextmanager

@contextmanager
def suppress_tf_logs():
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    stderr = sys.stderr
    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr = stderr