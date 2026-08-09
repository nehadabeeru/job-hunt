from .ashby import AshbyConnector
from .base import ATSConnector, FetchError
from .greenhouse import GreenhouseConnector
from .lever import LeverConnector
from .workday import WorkdayConnector

CONNECTORS: dict[str, ATSConnector] = {
    "greenhouse": GreenhouseConnector(),
    "lever": LeverConnector(),
    "ashby": AshbyConnector(),
    "workday": WorkdayConnector(),
}
