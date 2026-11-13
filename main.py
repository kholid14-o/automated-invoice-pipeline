import time 
from fastapi import FastAPI, File, UploadFile, Depends, BackgroundTasks 
from sqlalchemy.orm import Session
from database import engine, get_db, SessionLocal, Base 
from fastapi import FastAPI, File, UploadFile, Depends, BackgroundTasks, Response 
import pandas as pd 
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice Pipeline API")


def process_invoice_data(invoice_id: int):
    db = SessionLocal()
    try:
        time.sleep(10)
        
        invoice = db.query(models.InvoiceRecord).filter(models.InvoiceRecord.id == invoice_id).first()
        
        
        if invoice:
            invoice.status = "Completed"
            invoice.vendor_name = "PT. Teknologi Nusantara"
            invoice.transaction_date = "2023-10-25"
            invoice.total_amount = "Rp 15.000.000"
            db.commit()
    finally:
        db.close() 

@app.post('/api/upload-invoice')
async def upload_invoice(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None 
):
    if not file.filename.endswith('.pdf'):
        return {'error': 'sistem hanya menerima file PDF'}

    
    db_invoice = models.InvoiceRecord(filename=file.filename, status="Uploaded")
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    background_tasks.add_task(process_invoice_data, db_invoice.id)

    return {
        "status": "sukses",
        "invoice_id": db_invoice.id,
        "nama_file": file.filename,
        "pesan": "Payload file PDF diterima dan sedang diekstrak di latar belakang."
    }

# --- ENDPOINT BARU UNTUK CEK HASIL ---
@app.get('/api/invoice/{invoice_id}')
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    

    invoice = db.query(models.InvoiceRecord).filter(models.InvoiceRecord.id == invoice_id).first()
    
    
    if not invoice:
        return {"error": "Data invoice tidak ditemukan"}
        
    
    return {
        "id": invoice.id,
        "nama_file": invoice.filename,
        "status": invoice.status,
        "nama_vendor": invoice.vendor_name,
        "tanggal_transaksi": invoice.transaction_date,
        "total_tagihan": invoice.total_amount
    }

# --- ENDPOINT BARU UNTUK EXPORT DATA KE CSV ---
@app.get('/api/export-invoices')
def export_invoices(db: Session = Depends(get_db)):
    
    
    invoices = db.query(models.InvoiceRecord).all()
    
    if not invoices:
        return {"error": "Belum ada data untuk diekspor."}


    data_list = []
    for inv in invoices:
        data_list.append({
            "ID": inv.id,
            "Nama File": inv.filename,
            "Status": inv.status,
            "Nama Vendor": inv.vendor_name,
            "Tanggal": inv.transaction_date,
            "Total Tagihan": inv.total_amount
        })
        
    
    df = pd.DataFrame(data_list)
    csv_data = df.to_csv(index=False)
    
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rekap_invoice.csv"}
    )
