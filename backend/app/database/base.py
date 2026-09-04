"""
database/base.py
Every model in app/models/*.py inherits from this Base.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
