from datetime import datetime 
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship 
from database import Base 

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    transactions = relationship("Transaction", back_populates="product")

class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    cogs = Column(Float, nullable=False)            
    selling_price = Column(Float, nullable=False)   
    days_to_expire = Column(Integer, nullable=False)
    product = relationship("Product", back_populates="inventory")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    discount_applied = Column(Float, default=0.0, nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    product = relationship("Product", back_populates="transactions")