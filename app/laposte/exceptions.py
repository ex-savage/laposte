class LaposteError(Exception):
    message = "Something wrong on Laposte side"

    def __str__(self):
        return self.message


class InvalidTrackingNumber(LaposteError):
    message = "Invalid tracking number"


class UnauthorizedError(LaposteError):
    message = "Invalid Laposte API key or auth improperly configured"


class CorruptedData(LaposteError):
    message = "Cannot parse Laposte response: data corrupted"

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return f"{self.message}. Input data: {self.data}"
