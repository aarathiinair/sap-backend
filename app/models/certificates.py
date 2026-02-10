from datetime import datetime, timedelta
from typing import Optional
import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, event, case, and_
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.hybrid import hybrid_property

from app.db import Base


class CertificateStatus(str, enum.Enum):
    ACTIVE = "Active"
    EXPIRING_SOON = "Expiring Soon"
    EXPIRED = "Expired"


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    certificate_name: Mapped[str] = Column(String, nullable=False, unique=True)
    expiration_date: Mapped[datetime] = Column(DateTime, nullable=False)
    description: Mapped[Optional[str]] = Column(String, nullable=True)
    usage: Mapped[Optional[str]] = Column(String, nullable=True)
    impacted_servers: Mapped[Optional[str]] = Column(String, nullable=True)
    responsible_group: Mapped[str] = Column(String, nullable=False)
    teams_channel: Mapped[str] = Column(String, nullable=False)
    effected_users: Mapped[Optional[str]] = Column(String, nullable=True)

    calculated_status: Mapped[str] = Column(SQLEnum(CertificateStatus), default=CertificateStatus.ACTIVE, nullable=False)

    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now().replace(microsecond=0), nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now().replace(microsecond=0), onupdate=lambda: datetime.now().replace(microsecond=0), nullable=False)

    @hybrid_property
    def status(self) -> CertificateStatus:
        now = datetime.now().replace(microsecond=0)
        if self.expiration_date < now:
            return CertificateStatus.EXPIRED
        if (self.expiration_date - now).days <= 14:
            return CertificateStatus.EXPIRING_SOON
        return CertificateStatus.ACTIVE

    @status.expression
    def status(cls):
        now = datetime.now()
        soon = now + timedelta(days=14)
        return case(
            (cls.expiration_date < now, CertificateStatus.EXPIRED),
            (and_(cls.expiration_date >= now, cls.expiration_date <= soon), CertificateStatus.EXPIRING_SOON),
            else_=CertificateStatus.ACTIVE,
        )


@event.listens_for(Certificate, "load")
def update_certificate_status(target, context):
    now = datetime.now().replace(microsecond=0)
    expiry = target.expiration_date

    if expiry < now:
        target.calculated_status = CertificateStatus.EXPIRED.value
    elif (expiry - now).days <= 14:
        target.calculated_status = CertificateStatus.EXPIRING_SOON.value
    else:
        target.calculated_status = CertificateStatus.ACTIVE.value