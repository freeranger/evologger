# pylint: disable=C0103
class Temperature:
    """
    Represents a target and actual temperature in a zone
    """
    def __init__(self, zone, actual, target=None):
        self.zone = zone
        self.actual = actual
        self.target = target
