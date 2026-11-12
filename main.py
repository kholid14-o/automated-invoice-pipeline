import time # Tambahkan ini untuk simulasi waktu tunggu
from fastapi import FastAPI, File, UploadFile, Depends, BackgroundTasks # Tambahkan BackgroundTasks
from sqlalchemy.orm import Session
from database import engine, get_db, SessionLocal, Base # Tambahkan SessionLocal
from fastapi import FastAPI, File, UploadFile, Depends, BackgroundTasks, Response # Tambahkan Response
import pandas as pd # Tambahkan ini untuk mengolah data ekspor
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice Pipeline API")

# --- FUNGSI BARU UNTUK BACKGROUND TASK ---
def process_invoice_data(invoice_id: int):
    # Buka koneksi database baru khusus untuk tugas di latar belakang
    db = SessionLocal()
    try:
        # 1. Simulasi proses AI/OCR membaca PDF (sengaja kita perlambat 10 detik)
        time.sleep(10)
        
        # 2. Cari data invoice di database berdasarkan ID
        invoice = db.query(models.InvoiceRecord).filter(models.InvoiceRecord.id == invoice_id).first()
        
        # 3. Update data yang kosong dengan hasil "bacaan AI"
        if invoice:
            invoice.status = "Completed"
            invoice.vendor_name = "PT. Teknologi Nusantara"
            invoice.transaction_date = "2023-10-25"
            invoice.total_amount = "Rp 15.000.000"
            db.commit()
    finally:
        db.close() # Tutup koneksi agar rapi
# -----------------------------------------

@app.post('/api/upload-invoice')
async def upload_invoice(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None # Tambahkan parameter ini
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
    
    # 1. Cari data di database berdasarkan ID yang diminta
    invoice = db.query(models.InvoiceRecord).filter(models.InvoiceRecord.id == invoice_id).first()
    
    # 2. Jika ID tidak ditemukan di database
    if not invoice:
        return {"error": "Data invoice tidak ditemukan"}
        
    # 3. Jika ditemukan, tampilkan semua datanya
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
    
    # 1. Ambil seluruh data yang ada di tabel invoices
    invoices = db.query(models.InvoiceRecord).all()
    
    if not invoices:
        return {"error": "Belum ada data untuk diekspor."}

    # 2. Susun data menjadi format daftar (list) agar mudah dibaca Pandas
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
        
    # 3. Gunakan Pandas untuk mengubah data menjadi format tabel (DataFrame), lalu ke teks CSV
    df = pd.DataFrame(data_list)
    csv_data = df.to_csv(index=False)
    
    # 4. Berikan respons berupa file yang akan otomatis terunduh
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rekap_invoice.csv"}
    )