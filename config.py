import numpy as np

#BASE_URL = "https://firstjob.me/ofertas?semantic=a&type%5B%5D=1"
BASE_URL= "https://firstjob.me/ofertas?semantic=a"
FECHA_HOY = str(np.datetime64("today", "D"))

# Configuration
MAX_RETRIES = 3
MAX_CONCURRENT_REQUESTS = 5
RETRY_DELAY = 1.0
