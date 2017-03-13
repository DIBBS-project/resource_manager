import os
from .settings import *

DATABASES['default']['NAME'] = os.environ['TEMP_DATABASE']
