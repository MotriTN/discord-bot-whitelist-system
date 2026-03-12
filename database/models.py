from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger, Date
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True) # Discord User ID
    trust_charges = Column(Integer, default=2)
    report_charges = Column(Integer, default=2)
    last_reset_month = Column(Integer, default=0) # 1-12
    is_admin_whitelisted = Column(Boolean, default=False)
    is_admin_blacklisted = Column(Boolean, default=False)
    aura = Column(Integer, default=0)

    plans = relationship("DailyPlan", back_populates="user")
    trusts_given = relationship("Trust", foreign_keys="Trust.truster_id", back_populates="truster")
    trusts_received = relationship("Trust", foreign_keys="Trust.trustee_id", back_populates="trustee")
    reports_given = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    reports_received = relationship("Report", foreign_keys="Report.reported_id", back_populates="reported")

class Trust(Base):
    __tablename__ = "trusts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    truster_id = Column(BigInteger, ForeignKey("users.id"))
    trustee_id = Column(BigInteger, ForeignKey("users.id"))
    active = Column(Boolean, default=True)

    truster = relationship("User", foreign_keys=[truster_id], back_populates="trusts_given")
    trustee = relationship("User", foreign_keys=[trustee_id], back_populates="trusts_received")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reporter_id = Column(BigInteger, ForeignKey("users.id"))
    reported_id = Column(BigInteger, ForeignKey("users.id"))
    reason = Column(String, default="")
    active = Column(Boolean, default=True)

    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_given")
    reported = relationship("User", foreign_keys=[reported_id], back_populates="reports_received")

class DailyPlan(Base):
    __tablename__ = "daily_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    objective = Column(String, nullable=False)
    habit = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    is_reviewed = Column(Boolean, default=False)
    status = Column(String, nullable=True) # "victory" or "defeat"

    user = relationship("User", back_populates="plans")
