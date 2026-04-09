"""
Tempoblock - Temporarily block distracting websites and apps

Author: Joel Claw
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Joel Claw"

from .blocker import Blocker
from .timer import Timer

__all__ = ["Blocker", "Timer"]