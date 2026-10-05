from simpro_client.rate_limiter import TokenBucket


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

def test_burst_refill_and_wait():
    fake = FakeTime()
    bucket = TokenBucket(2.0, 2, clock=fake.clock, sleeper=fake.sleep)
    bucket.acquire()
    bucket.acquire()
    assert fake.sleeps == []
    bucket.acquire()
    assert fake.sleeps == [0.5]
def test_lock_is_released_before_sleep():
    fake = FakeTime()
    bucket = TokenBucket(1.0, 1, clock=fake.clock, sleeper=fake.sleep)
    bucket.acquire()

    def sleep(seconds):
        assert bucket._lock.acquire(blocking=False)
        bucket._lock.release()
        fake.sleep(seconds)

    bucket._sleeper = sleep
    bucket.acquire()
    assert fake.sleeps == [1.0]
