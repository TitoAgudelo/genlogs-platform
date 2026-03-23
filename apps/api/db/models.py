from sqlalchemy import Column, Integer, String
from db.database import Base


class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(String, primary_key=True)
    truck_id = Column(String, nullable=False)
    carrier_name = Column(String, nullable=False)
    origin_city = Column(String, nullable=False)
    destination_city = Column(String, nullable=False)
    trucks_per_day = Column(Integer, nullable=False)
    trip_date = Column(String, nullable=False)
