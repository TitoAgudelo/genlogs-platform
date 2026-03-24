from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(String, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    highway_name = Column(String, nullable=False)

    images = relationship("ImageTransaction", back_populates="camera")


class ImageTransaction(Base):
    __tablename__ = "image_transactions"

    image_id = Column(String, primary_key=True)
    camera_id = Column(String, ForeignKey("cameras.camera_id"), nullable=False)
    timestamp = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    weather_conditions = Column(String, nullable=True)
    vehicle_speed = Column(Float, nullable=True)

    camera = relationship("Camera", back_populates="images")
    processing_results = relationship("ImageProcessingResult", back_populates="image")
    sightings = relationship("TruckSighting", back_populates="image")


class ImageProcessingResult(Base):
    __tablename__ = "image_processing_results"

    result_id = Column(String, primary_key=True)
    image_id = Column(String, ForeignKey("image_transactions.image_id"), nullable=False)
    analysis_type = Column(String, nullable=False)  # plate, logo, truck_number
    detected_value = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)

    image = relationship("ImageTransaction", back_populates="processing_results")


class Carrier(Base):
    __tablename__ = "carriers"

    carrier_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    usdot_number = Column(String, nullable=False)
    headquarters_city = Column(String, nullable=False)

    trucks = relationship("Truck", back_populates="carrier")
    trips = relationship("Trip", back_populates="carrier")


class Truck(Base):
    __tablename__ = "trucks"

    truck_id = Column(String, primary_key=True)
    license_plate = Column(String, nullable=False)
    usdot_number = Column(String, nullable=False)
    carrier_id = Column(String, ForeignKey("carriers.carrier_id"), nullable=False)

    carrier = relationship("Carrier", back_populates="trucks")
    sightings = relationship("TruckSighting", back_populates="truck")
    trips = relationship("Trip", back_populates="truck")


class TruckSighting(Base):
    __tablename__ = "truck_sightings"

    sighting_id = Column(String, primary_key=True)
    truck_id = Column(String, ForeignKey("trucks.truck_id"), nullable=False)
    image_id = Column(String, ForeignKey("image_transactions.image_id"), nullable=False)
    timestamp = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)

    truck = relationship("Truck", back_populates="sightings")
    image = relationship("ImageTransaction", back_populates="sightings")


class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(String, primary_key=True)
    truck_id = Column(String, ForeignKey("trucks.truck_id"), nullable=False)
    carrier_id = Column(String, ForeignKey("carriers.carrier_id"), nullable=False)
    origin_city = Column(String, nullable=False)
    destination_city = Column(String, nullable=False)
    trip_date = Column(String, nullable=False)

    truck = relationship("Truck", back_populates="trips")
    carrier = relationship("Carrier", back_populates="trips")
