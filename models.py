from sqlalchemy import Column, Integer, String
from database import Base

class InvoiceRecord(Base):
    __tablename__ = "invoices"

    # Gunakan huruf kecil "index=True", bukan "Index=True"
    id = Column(Integer, primary_key=True, index=True)
    
    # Bagian ini juga dipastikan menggunakan huruf kecil
    filename = Column(String, index=True)
    status = Column(String, default="Uploaded")

    vendor_name = Column(String, nullable=True)
    transaction_date = Column(String, nullable=True)
    total_amount = Column(String, nullable=True)