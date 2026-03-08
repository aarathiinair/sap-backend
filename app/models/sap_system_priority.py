from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import Mapped

from app.db import Base


class SapSystemPriority(Base):
    __tablename__ = "sap_system_priority"

    system_number: Mapped[str] = Column(String, primary_key=True, nullable=False)
    system_id: Mapped[Optional[str]] = Column(String, nullable=True)
    system_name: Mapped[Optional[str]] = Column(String, nullable=True)
    system_role: Mapped[Optional[str]] = Column(String, nullable=True)
    deployment_model: Mapped[Optional[str]] = Column(String, nullable=True)
    installation_name: Mapped[Optional[str]] = Column(String, nullable=True)
    installation_number: Mapped[Optional[str]] = Column(String, nullable=True)
    software_product: Mapped[Optional[str]] = Column(String, nullable=True)
    priority_level: Mapped[Optional[str]] = Column(String, nullable=True)

    is_active: Mapped[Optional[bool]] = Column(Boolean, nullable=True)
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime,
        default=lambda: datetime.now().replace(microsecond=0),
        onupdate=lambda: datetime.now().replace(microsecond=0),
        nullable=True
    )

    def __repr__(self):
        return f"<SapSystemPriority(system_number='{self.system_number}', system_name='{self.system_name}')>"