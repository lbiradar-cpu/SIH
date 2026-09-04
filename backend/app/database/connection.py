"""
database/connection.py
Engine + session setup, get_db() dependency for routes, init_db() called
once at startup to create tables and seed the initial rule set.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models so they're registered on Base.metadata before create_all.
    from app.models import user, inspection, declaration, violation, rule, evidence  # noqa: F401

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        _seed_rules(db)
    finally:
        db.close()


def _seed_rules(db):
    from app.models.rule import Rule

    if db.query(Rule).count() > 0:
        return

    # Mandatory declarations required under the Legal Metrology (Packaged
    # Commodities) Rules, 2011, Rule 6 - kept as structured, versioned data
    # rather than hardcoded logic, so it can be amended without code changes.
    seed = [
        Rule(
            rule_code="LMPC-R6-MFR",
            field_name="manufacturer",
            description="Name and address of the manufacturer/packer/importer",
            requirement="required_present",
            source_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6",
            version="2011",
            active=True,
        ),
        Rule(
            rule_code="LMPC-R6-COMMON-NAME",
            field_name="common_name",
            description="Common or generic name of the commodity",
            requirement="required_present",
            source_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6",
            version="2011",
            active=True,
        ),
        Rule(
            rule_code="LMPC-R6-NET-QTY",
            field_name="net_quantity",
            description="Net quantity in standard units (weight/volume/number)",
            requirement="required_present_with_unit",
            source_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6 & Rule 18",
            version="2011",
            active=True,
        ),
        Rule(
            rule_code="LMPC-R6-MRP",
            field_name="mrp",
            description="Retail sale price, inclusive of all taxes (MRP)",
            requirement="required_present",
            source_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6",
            version="2011",
            active=True,
        ),
        Rule(
            rule_code="LMPC-R6-MFG-DATE",
            field_name="mfg_date",
            description="Month and year of manufacture/packing/import",
            requirement="required_present",
            source_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6",
            version="2011",
            active=True,
        ),
        Rule(
            rule_code="LMPC-R6-CONSUMER-CARE",
            field_name="consumer_care",
            description="Consumer care / customer support contact details",
            requirement="required_present",
            source_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6",
            version="2011",
            active=True,
        ),
    ]
    db.add_all(seed)
    db.commit()
