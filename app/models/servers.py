from app.db import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped

class Server(Base):
    """
    Database model for storing server/computer information, grouped by function.
    """
    __tablename__ = "servers"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    computername: Mapped[str] = Column(String, index=True, nullable=False)
    group: Mapped[str] = Column(String, index=True, nullable=False)
    description_function: Mapped[str] = Column(String, nullable=True)
    responsible_person: Mapped[str] = Column(String, nullable=True)

    def __repr__(self):
        return f"<Server(computername='{self.computername}', group='{self.group}')>"