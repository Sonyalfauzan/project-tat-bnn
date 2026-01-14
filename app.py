"""
=================================================================================
SISTEM ASESMEN TERPADU BNN PROVINSI KALIMANTAN UTARA
=================================================================================
Tools bantu untuk proses asesmen narkotika berdasarkan:
- UU No. 35 Tahun 2009 tentang Narkotika
- Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014
- Perka BNN No. 11 Tahun 2014
- Keputusan Kepala BNN No. KEP/99 I/X/KA/PB/06.00/2025/BNN tentang Petunjuk Teknis Pelaksanaan Asesmen Terpadu
- Instrumen Asesmen: ASI, ASAM, PPDGJ III, ICD-10

CATATAN PENTING:
Sistem ini adalah ALAT BANTU untuk Tim Asesmen Terpadu.
Keputusan final tetap ada di tangan BNN dan aparat penegak hukum.
=================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import json
import io
import base64
from io import BytesIO
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pythoncom
import win32com.client

# =============================================================================
# KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="Sistem Asesmen Terpadu - BNN Provinsi Kalimantan Utara",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2a5298;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1e3c72;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .section-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# KONSTANTA DAN KONFIGURASI
# =============================================================================

# Informasi BNN Provinsi Kalimantan Utara
BNN_INFO = {
    "nama": "BADAN NARKOTIKA NASIONAL PROVINSI KALIMANTAN UTARA",
    "alamat": "Jl. Teuku Umar No. 31, Kota Tarakan, Provinsi Kalimantan Utara",
    "telepon": "(0551) 1234567",
    "fax": "(0551) 1234568",
    "email": "bnn.kalut@bnn.go.id",
    "website": "www.bnn.go.id/kalimantan-utara"
}

# Gramatur berdasarkan SEMA 4/2010
GRAMATUR_LIMITS = {
    "Ganja/Cannabis": 5.0,
    "Metamfetamin/Sabu": 1.0,
    "Heroin": 1.8,
    "Kokain": 1.8,
    "Ekstasi/MDMA": 2.4,
    "Morfin": 1.8,
    "Kodein": 72.0,
    "Carisoprodol": 10.0,
    "Cannabinoid Sintesis": 2.0,
    "Lainnya": 1.0
}

# Jenis-jenis narkotika untuk tes urine
JENIS_NARKOTIKA = [
    "Metamfetamin (MET/Sabu)",
    "Morfin (MOP/Heroin)",
    "Kokain (COC)",
    "Amfetamin (AMP)",
    "Benzodiazepin (BZO)",
    "THC (Ganja)",
    "MDMA (Ekstasi)",
    "Carisoprodol",
    "Cannabinoid Sintesis",
    "Lainnya"
]

# Kriteria ASAM 6 Dimensi
ASAM_DIMENSIONS = [
    "1. Kondisi Intoksikasi/Withdrawal Akut",
    "2. Kondisi Biomedis",
    "3. Kondisi Emosional, Perilaku, dan Kognitif",
    "4. Kesiapan Berubah",
    "5. Potensi Relaps",
    "6. Lingkungan Pemulihan"
]

# Kriteria PPDGJ III untuk Gangguan Penggunaan Zat
PPDGJ_CRITERIA = [
    "Gangguan Mental dan Perilaku akibat Penggunaan Opioid (F11)",
    "Gangguan Mental dan Perilaku akibat Penggunaan Cannabinoid (F12)",
    "Gangguan Mental dan Perilaku akibat Penggunaan Sedatif/Hipnotik (F13)",
    "Gangguan Mental dan Perilaku akibat Penggunaan Kokain (F14)",
    "Gangguan Mental dan Perilaku akibat Penggunaan Stimulan Lain (F15)",
    "Gangguan Mental dan Perilaku akibat Penggunaan Halusinogen (F16)",
    "Gangguan Mental dan Perilaku akibat Penggunaan Nikotin (F17)",
    "Gangguan Mental dan Perilaku akibat Penggunaan Zat Lain (F19)"
]

# Status Pernikahan
STATUS_PERKAWINAN = [
    "Belum Menikah",
    "Menikah",
    "Cerai Hidup",
    "Cerai Mati"
]

# Pendidikan Terakhir
PENDIDIKAN = [
    "Tidak Sekolah",
    "SD/Sederajat",
    "SMP/Sederajat",
    "SMA/Sederajat",
    "Diploma",
    "Sarjana",
    "Pascasarjana"
]

# =============================================================================
# FUNGSI GENERATE SURAT (WORD)
# =============================================================================

def generate_word_document(data_asesmen, hasil_analisis):
    """Membuat dokumen Word sesuai template surat BNN"""
    doc = Document()
    
    # Setup page
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    
    # Header dengan logo BNN (dalam aplikasi nyata, logo akan diunggah)
    header = section.header
    header_para = header.paragraphs[0]
    header_run = header_para.add_run()
    # Logo akan ditambahkan jika ada file, untuk sekarang teks saja
    header_para.add_run(f"{BNN_INFO['nama']}\n")
    header_para.add_run(f"{BNN_INFO['alamat']}\n")
    header_para.add_run(f"Telepon: {BNN_INFO['telepon']} | Fax: {BNN_INFO['fax']}\n")
    header_para.add_run(f"Email: {BNN_INFO['email']} | Website: {BNN_INFO['website']}")
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Judul Surat
    doc.add_heading('SURAT HASIL ASESMEN TERPADU', 0)
    doc.add_paragraph(f"Nomor: {hasil_analisis.get('nomor_surat', '-')}")
    doc.add_paragraph(f"Tanggal: {datetime.now().strftime('%d %B %Y')}")
    doc.add_paragraph("Klasifikasi: RAHASIA")
    doc.add_paragraph("Lampiran: 1 (satu) berkas Berita Acara Asesmen Terpadu")
    doc.add_paragraph(f"Perihal: Hasil Asesmen Terpadu terhadap {data_asesmen['demografi']['nama']}")
    
    doc.add_paragraph()
    
    # Alamat Tujuan
    doc.add_paragraph("Kepada Yth.")
    doc.add_paragraph("Direktur Tindak Pidana Narkoba Bareskrim Polri")
    doc.add_paragraph("di")
    doc.add_paragraph("Tempat")
    
    doc.add_paragraph()
    
    # Isi Surat
    # 1. Rujukan
    doc.add_heading('1. Rujukan:', level=1)
    rujukan = doc.add_paragraph()
    rujukan.add_run("a. Undang-Undang Nomor 35 Tahun 2009 tentang Narkotika;\n")
    rujukan.add_run("b. Peraturan Presiden Nomor 47 Tahun 2019 tentang Perubahan atas Peraturan Presiden Nomor 23 Tahun 2010 tentang Badan Narkotika Nasional;\n")
    rujukan.add_run("c. Peraturan Kepala BNN Nomor KEP/99 I/X/KA/PB/06.00/2025/BNN tentang Petunjuk Teknis Pelaksanaan Asesmen Terpadu;\n")
    rujukan.add_run("d. Peraturan Bersama 7 Instansi Tahun 2014 tentang Penanganan Pecandu dan Korban Penyalahgunaan Narkotika;\n")
    rujukan.add_run("e. Surat permohonan asesmen dari penyidik.")
    
    doc.add_paragraph()
    
    # 2. Pelaksanaan Asesmen
    doc.add_heading('2. Pelaksanaan Asesmen:', level=1)
    doc.add_paragraph(f"Tim Asesmen Terpadu BNN Provinsi Kalimantan Utara telah melaksanakan asesmen pada tanggal {hasil_analisis.get('tanggal_asesmen', '-')} terhadap:")
    
    # Data Tersangka
    table_data = doc.add_table(rows=6, cols=2)
    table_data.style = 'Table Grid'
    
    data_fields = [
        ("Nama", data_asesmen['demografi']['nama']),
        ("NIK", data_asesmen['demografi']['nik']),
        ("Tempat/Tgl Lahir", f"{data_asesmen['demografi']['tempat_lahir']}, {data_asesmen['demografi']['tanggal_lahir'].strftime('%d-%m-%Y')}"),
        ("Jenis Kelamin", data_asesmen['demografi']['jenis_kelamin']),
        ("Kewarganegaraan", data_asesmen['demografi']['kewarganegaraan']),
        ("Alamat", data_asesmen['demografi']['alamat'])
    ]
    
    for i, (field, value) in enumerate(data_fields):
        row = table_data.rows[i]
        row.cells[0].text = field
        row.cells[1].text = str(value)
    
    doc.add_paragraph()
    
    # 3. Hasil Asesmen
    doc.add_heading('3. Hasil Asesmen:', level=1)
    
    # Hasil Medis
    doc.add_heading('a. Asesmen Medis:', level=2)
    doc.add_paragraph(f"Berdasarkan hasil pemeriksaan medis dan psikologis menggunakan instrumen ASAM, PPDGJ III, dan ICD-10, diperoleh hasil sebagai berikut:")
    
    medis_hasil = doc.add_table(rows=4, cols=2)
    medis_hasil.style = 'Table Grid'
    
    medis_fields = [
        ("Jenis Narkotika", ", ".join(data_asesmen['narkotika']['jenis_narkotika'])),
        ("Hasil Tes Urine", data_asesmen['narkotika']['hasil_urine']),
        ("Durasi Penggunaan", f"{data_asesmen['narkotika']['durasi_penggunaan']} bulan"),
        ("Diagnosis Medis", hasil_analisis.get('diagnosis_medis', 'Sedang dievaluasi'))
    ]
    
    for i, (field, value) in enumerate(medis_fields):
        row = medis_hasil.rows[i]
        row.cells[0].text = field
        row.cells[1].text = str(value)
    
    # Hasil Hukum
    doc.add_heading('b. Asesmen Hukum:', level=2)
    doc.add_paragraph("Berdasarkan hasil pemeriksaan hukum dan verifikasi data intelijen:")
    
    hukum_hasil = doc.add_table(rows=4, cols=2)
    hukum_hasil.style = 'Table Grid'
    
    hukum_fields = [
        ("Barang Bukti", f"{data_asesmen['hukum']['barang_bukti']} gram {data_asesmen['hukum']['jenis_narkotika']}"),
        ("Keterlibatan Jaringan", data_asesmen['hukum']['keterlibatan_jaringan']),
        ("Riwayat Pidana", data_asesmen['hukum']['riwayat_pidana']),
        ("Status Penangkapan", data_asesmen['hukum']['status_penangkapan'])
    ]
    
    for i, (field, value) in enumerate(hukum_fields):
        row = hukum_hasil.rows[i]
        row.cells[0].text = field
        row.cells[1].text = str(value)
    
    doc.add_paragraph()
    
    # 4. Kesimpulan
    doc.add_heading('4. Kesimpulan:', level=1)
    doc.add_paragraph(hasil_analisis.get('kesimpulan', 'Sedang diproses'))
    
    doc.add_paragraph()
    
    # 5. Rekomendasi
    doc.add_heading('5. Rekomendasi:', level=1)
    doc.add_paragraph(hasil_analisis.get('rekomendasi', 'Sedang diproses'))
    
    doc.add_paragraph()
    
    # Penutup
    doc.add_paragraph("Demikian surat ini dibuat untuk dapat dipergunakan sebagaimana mestinya.")
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    # Tanda Tangan
    tanda_tangan = doc.add_table(rows=1, cols=1)
    tanda_tangan.style = 'Table Grid'
    row = tanda_tangan.rows[0]
    row.cells[0].text = f"Direktur Pengawasan Tahanan dan Barang Bukti BNN Provinsi Kalimantan Utara\n\n\n\n(_________________________)"
    row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Tembusan
    doc.add_page_break()
    doc.add_heading('Tembusan:', level=1)
    tembusan = [
        "1. Kepala BNN Pusat",
        "2. Sekretaris Utama BNN",
        "3. Deputi Rehabilitasi BNN",
        "4. Kepala BNN Provinsi Kalimantan Utara",
        "5. Kabareskrim Polri",
        "6. Arsip"
    ]
    
    for item in tembusan:
        doc.add_paragraph(item)
    
    # Simpan ke BytesIO
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    
    return file_stream

# =============================================================================
# FUNGSI GENERATE SURAT (PDF)
# =============================================================================

def generate_pdf_document(data_asesmen, hasil_analisis):
    """Membuat dokumen PDF sesuai template surat BNN"""
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5*cm,
        leftMargin=2.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Judul Surat
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Title'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    elements.append(Paragraph(f"{BNN_INFO['nama']}", title_style))
    elements.append(Paragraph(f"{BNN_INFO['alamat']}", styles['Normal']))
    elements.append(Paragraph(f"Telepon: {BNN_INFO['telepon']} | Fax: {BNN_INFO['fax']}", styles['Normal']))
    elements.append(Paragraph(f"Email: {BNN_INFO['email']} | Website: {BNN_INFO['website']}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Judul Surat
    elements.append(Paragraph("SURAT HASIL ASESMEN TERPADU", title_style))
    elements.append(Spacer(1, 12))
    
    # Nomor dan tanggal
    elements.append(Paragraph(f"Nomor: {hasil_analisis.get('nomor_surat', '-')}", styles['Normal']))
    elements.append(Paragraph(f"Tanggal: {datetime.now().strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Paragraph("Klasifikasi: RAHASIA", styles['Normal']))
    elements.append(Paragraph("Lampiran: 1 (satu) berkas Berita Acara Asesmen Terpadu", styles['Normal']))
    elements.append(Paragraph(f"Perihal: Hasil Asesmen Terpadu terhadap {data_asesmen['demografi']['nama']}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Alamat tujuan
    elements.append(Paragraph("Kepada Yth.", styles['Normal']))
    elements.append(Paragraph("Direktur Tindak Pidana Narkoba Bareskrim Polri", styles['Normal']))
    elements.append(Paragraph("di", styles['Normal']))
    elements.append(Paragraph("Tempat", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Rujukan
    elements.append(Paragraph("1. Rujukan:", styles['Heading2']))
    rujukan_text = """
    a. Undang-Undang Nomor 35 Tahun 2009 tentang Narkotika;
    b. Peraturan Presiden Nomor 47 Tahun 2019 tentang Perubahan atas Peraturan Presiden Nomor 23 Tahun 2010 tentang Badan Narkotika Nasional;
    c. Peraturan Kepala BNN Nomor KEP/99 I/X/KA/PB/06.00/2025/BNN tentang Petunjuk Teknis Pelaksanaan Asesmen Terpadu;
    d. Peraturan Bersama 7 Instansi Tahun 2014 tentang Penanganan Pecandu dan Korban Penyalahgunaan Narkotika;
    e. Surat permohonan asesmen dari penyidik.
    """
    elements.append(Paragraph(rujukan_text, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Pelaksanaan Asesmen
    elements.append(Paragraph("2. Pelaksanaan Asesmen:", styles['Heading2']))
    elements.append(Paragraph(f"Tim Asesmen Terpadu BNN Provinsi Kalimantan Utara telah melaksanakan asesmen pada tanggal {hasil_analisis.get('tanggal_asesmen', '-')} terhadap:", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Data Tersangka dalam tabel
    data_tersangka = [
        ["Nama", data_asesmen['demografi']['nama']],
        ["NIK", data_asesmen['demografi']['nik']],
        ["Tempat/Tgl Lahir", f"{data_asesmen['demografi']['tempat_lahir']}, {data_asesmen['demografi']['tanggal_lahir'].strftime('%d-%m-%Y')}"],
        ["Jenis Kelamin", data_asesmen['demografi']['jenis_kelamin']],
        ["Kewarganegaraan", data_asesmen['demografi']['kewarganegaraan']],
        ["Alamat", data_asesmen['demografi']['alamat']]
    ]
    
    table = Table(data_tersangka, colWidths=[4*cm, 10*cm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Hasil Asesmen
    elements.append(Paragraph("3. Hasil Asesmen:", styles['Heading2']))
    elements.append(Paragraph("a. Asesmen Medis:", styles['Heading3']))
    elements.append(Paragraph("Berdasarkan hasil pemeriksaan medis dan psikologis menggunakan instrumen ASAM, PPDGJ III, dan ICD-10, diperoleh hasil sebagai berikut:", styles['Normal']))
    
    data_medis = [
        ["Jenis Narkotika", ", ".join(data_asesmen['narkotika']['jenis_narkotika'])],
        ["Hasil Tes Urine", data_asesmen['narkotika']['hasil_urine']],
        ["Durasi Penggunaan", f"{data_asesmen['narkotika']['durasi_penggunaan']} bulan"],
        ["Diagnosis Medis", hasil_analisis.get('diagnosis_medis', 'Sedang dievaluasi')]
    ]
    
    table_medis = Table(data_medis, colWidths=[5*cm, 9*cm])
    table_medis.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(table_medis)
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("b. Asesmen Hukum:", styles['Heading3']))
    elements.append(Paragraph("Berdasarkan hasil pemeriksaan hukum dan verifikasi data intelijen:", styles['Normal']))
    
    data_hukum = [
        ["Barang Bukti", f"{data_asesmen['hukum']['barang_bukti']} gram {data_asesmen['hukum']['jenis_narkotika']}"],
        ["Keterlibatan Jaringan", data_asesmen['hukum']['keterlibatan_jaringan']],
        ["Riwayat Pidana", data_asesmen['hukum']['riwayat_pidana']],
        ["Status Penangkapan", data_asesmen['hukum']['status_penangkapan']]
    ]
    
    table_hukum = Table(data_hukum, colWidths=[5*cm, 9*cm])
    table_hukum.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(table_hukum)
    elements.append(Spacer(1, 20))
    
    # Kesimpulan
    elements.append(Paragraph("4. Kesimpulan:", styles['Heading2']))
    elements.append(Paragraph(hasil_analisis.get('kesimpulan', 'Sedang diproses'), styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Rekomendasi
    elements.append(Paragraph("5. Rekomendasi:", styles['Heading2']))
    elements.append(Paragraph(hasil_analisis.get('rekomendasi', 'Sedang diproses'), styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Penutup
    elements.append(Paragraph("Demikian surat ini dibuat untuk dapat dipergunakan sebagaimana mestinya.", styles['Normal']))
    elements.append(Spacer(1, 40))
    
    # Tanda tangan
    tanda_tangan = Table([[Paragraph("Direktur Pengawasan Tahanan dan Barang Bukti<br/>BNN Provinsi Kalimantan Utara<br/><br/><br/><br/>(_________________________)", 
                                     ParagraphStyle(name='Signature', alignment=TA_CENTER))]], 
                         colWidths=[14*cm])
    elements.append(tanda_tangan)
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# =============================================================================
# FUNGSI ANALISIS MEDIS
# =============================================================================

def analisis_medis(data_narkotika, data_medis):
    """Melakukan analisis medis berdasarkan data input"""
    
    hasil = {
        'diagnosis': '',
        'tingkat_kecanduan': '',
        'rekomendasi_medis': '',
        'skor_asam': 0,
        'kriteria_ppdgj': []
    }
    
    # Analisis berdasarkan jenis narkotika
    jenis_narkotika = data_narkotika['jenis_narkotika']
    durasi = data_narkotika['durasi_penggunaan']
    hasil_urine = data_narkotika['hasil_urine']
    
    # Menentukan diagnosis berdasarkan ICD-10
    if 'Sabu' in str(jenis_narkotika) or 'Metamfetamin' in str(jenis_narkotika):
        hasil['diagnosis'] = "F15 - Gangguan Mental dan Perilaku akibat Penggunaan Stimulan Lain"
    elif 'Ganja' in str(jenis_narkotika) or 'THC' in str(jenis_narkotika):
        hasil['diagnosis'] = "F12 - Gangguan Mental dan Perilaku akibat Penggunaan Cannabinoid"
    elif 'Heroin' in str(jenis_narkotika) or 'Morfin' in str(jenis_narkotika):
        hasil['diagnosis'] = "F11 - Gangguan Mental dan Perilaku akibat Penggunaan Opioid"
    elif 'Ekstasi' in str(jenis_narkotika) or 'MDMA' in str(jenis_narkotika):
        hasil['diagnosis'] = "F15 - Gangguan Mental dan Perilaku akibat Penggunaan Stimulan Lain"
    else:
        hasil['diagnosis'] = "F19 - Gangguan Mental dan Perilaku akibat Penggunaan Zat Lain"
    
    # Menentukan tingkat kecanduan berdasarkan durasi
    if durasi < 6:
        hasil['tingkat_kecanduan'] = "Ringan"
        hasil['skor_asam'] = 2
    elif durasi <= 12:
        hasil['tingkat_kecanduan'] = "Sedang"
        hasil['skor_asam'] = 4
    else:
        hasil['tingkat_kecanduan'] = "Berat"
        hasil['skor_asam'] = 6
    
    # Rekomendasi medis
    if hasil['tingkat_kecanduan'] == "Ringan":
        hasil['rekomendasi_medis'] = "Rehabilitasi Rawat Jalan dengan monitoring rutin"
    elif hasil['tingkat_kecanduan'] == "Sedang":
        hasil['rekomendasi_medis'] = "Rehabilitasi Rawat Inap intensif 3-6 bulan"
    else:
        hasil['rekomendasi_medis'] = "Rehabilitasi Rawat Inap intensif 6-12 bulan dengan terapi medis khusus"
    
    return hasil

# =============================================================================
# FUNGSI ANALISIS HUKUM
# =============================================================================

def analisis_hukum(data_hukum, data_narkotika):
    """Melakukan analisis hukum berdasarkan data input"""
    
    hasil = {
        'kategori_hukum': '',
        'rekomendasi_hukum': '',
        'indikasi_jaringan': '',
        'kesimpulan_hukum': ''
    }
    
    # Analisis berdasarkan barang bukti dan keterlibatan
    barang_bukti = data_hukum['barang_bukti']
    jenis_narkotika = data_hukum['jenis_narkotika']
    keterlibatan = data_hukum['keterlibatan_jaringan']
    gramatur_limit = GRAMATUR_LIMITS.get(jenis_narkotika, 1.0)
    
    # Menentukan kategori hukum
    if barang_bukti < gramatur_limit and keterlibatan == "Untuk diri sendiri":
        hasil['kategori_hukum'] = "Pengguna"
        hasil['rekomendasi_hukum'] = "Direhabilitasi sesuai rekomendasi medis"
        hasil['indikasi_jaringan'] = "Tidak ditemukan indikasi keterlibatan jaringan"
    elif barang_bukti < gramatur_limit * 5 and keterlibatan in ["Untuk diri sendiri", "Dipakai bersama-sama"]:
        hasil['kategori_hukum'] = "Penyalahguna"
        hasil['rekomendasi_hukum'] = "Direhabilitasi dengan proses hukum ringan"
        hasil['indikasi_jaringan'] = "Minimal indikasi keterlibatan jaringan"
    else:
        hasil['kategori_hukum'] = "Pengedar"
        hasil['rekomendasi_hukum'] = "Proses hukum pidana dengan rehabilitasi"
        hasil['indikasi_jaringan'] = "Ada indikasi keterlibatan jaringan"
    
    # Kesimpulan hukum
    if data_hukum['riwayat_pidana'] == "First offender (pertama kali)":
        riwayat_text = "Tidak ada riwayat pidana sebelumnya"
    else:
        riwayat_text = f"Ada riwayat: {data_hukum['riwayat_pidana']}"
    
    hasil['kesimpulan_hukum'] = f"{hasil['kategori_hukum']} dengan {riwayat_text}. {hasil['indikasi_jaringan']}."
    
    return hasil

# =============================================================================
# FUNGSI UTAMA APLIKASI
# =============================================================================

def main():
    # Header
    st.markdown(f'<h1 class="main-header">SISTEM ASESMEN TERPADU</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{BNN_INFO["nama"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align: center; color: #666;">{BNN_INFO["alamat"]}</p>', unsafe_allow_html=True)
    
    # Peringatan
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ PERHATIAN PENTING:</strong><br>
        Sistem ini adalah <strong>ALAT BANTU</strong> untuk proses asesmen.
        Keputusan final tetap berada di tangan <strong>Tim Asesmen Terpadu BNN</strong>
        dan aparat penegak hukum yang berwenang.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Dasar Hukum")
        st.markdown("""
        **Regulasi yang Digunakan:**
        - UU No. 35 Tahun 2009 tentang Narkotika
        - Keputusan Kepala BNN No. KEP/99 I/X/KA/PB/06.00/2025/BNN
        - Peraturan Bersama 7 Instansi (2014)
        - Perka BNN No. 11 Tahun 2014
        
        **Instrumen Asesmen:**
        - ASI (Addiction Severity Index)
        - ASAM (6 Dimensi)
        - PPDGJ III
        - ICD-10
        """)
        st.markdown("---")
        st.info("**Versi:** 2.0.0\n\n**Update:** Januari 2026")
    
    # Inisialisasi session state
    if 'data_asesmen' not in st.session_state:
        st.session_state.data_asesmen = {
            'demografi': {},
            'kronologi': {},
            'narkotika': {},
            'hukum': {},
            'medis': {}
        }
    
    if 'hasil_analisis' not in st.session_state:
        st.session_state.hasil_analisis = {}
    
    # Tab utama
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👤 DEMOGRAFI",
        "📜 KRONOLOGI",
        "💊 NARKOTIKA",
        "⚖️ HUKUM",
        "🏥 MEDIS",
        "📊 HASIL",
        "📄 SURAT"
    ])
    
    # ======================================================================
    # TAB 1: DATA DEMOGRAFI
    # ======================================================================
    with tab1:
        st.header("I. DATA DEMOGRAFI")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Informasi Pribadi")
            nama = st.text_input("Nama Lengkap*", key="nama")
            nik = st.text_input("NIK*", key="nik")
            tempat_lahir = st.text_input("Tempat Lahir*", key="tempat_lahir")
            tanggal_lahir = st.date_input("Tanggal Lahir*", value=date(1990, 1, 1), key="tanggal_lahir")
            jenis_kelamin = st.selectbox("Jenis Kelamin*", ["Laki-laki", "Perempuan"], key="jenis_kelamin")
            kewarganegaraan = st.text_input("Kewarganegaraan*", value="Indonesia", key="kewarganegaraan")
        
        with col2:
            st.subheader("Informasi Kontak & Sosial")
            alamat = st.text_area("Alamat Lengkap*", key="alamat")
            no_hp = st.text_input("Nomor Handphone*", key="no_hp")
            no_rekening = st.text_input("Nomor Rekening", key="no_rekening")
            status_perkawinan = st.selectbox("Status Perkawinan*", STATUS_PERKAWINAN, key="status_perkawinan")
            pendidikan = st.selectbox("Pendidikan Terakhir*", PENDIDIKAN, key="pendidikan")
            pekerjaan = st.text_input("Pekerjaan*", key="pekerjaan")
            penghasilan = st.number_input("Rata-rata Penghasilan per Bulan (Rp)*", min_value=0, value=3000000, key="penghasilan")
        
        catatan = st.text_area("Catatan Tambahan", key="catatan_demografi")
        
        if st.button("Simpan Data Demografi", type="primary"):
            st.session_state.data_asesmen['demografi'] = {
                'nama': nama,
                'nik': nik,
                'tempat_lahir': tempat_lahir,
                'tanggal_lahir': tanggal_lahir,
                'jenis_kelamin': jenis_kelamin,
                'kewarganegaraan': kewarganegaraan,
                'alamat': alamat,
                'no_hp': no_hp,
                'no_rekening': no_rekening,
                'status_perkawinan': status_perkawinan,
                'pendidikan': pendidikan,
                'pekerjaan': pekerjaan,
                'penghasilan': penghasilan,
                'catatan': catatan
            }
            st.success("Data demografi tersimpan!")
    
    # ======================================================================
    # TAB 2: KRONOLOGI KEJADIAN
    # ======================================================================
    with tab2:
        st.header("II. KRONOLOGI KEJADIAN")
        kronologi = st.text_area("Ceritakan kronologi kejadian secara lengkap*", 
                               height=200,
                               placeholder="Jelaskan bagaimana klien terlibat dalam kasus ini, mulai dari awal hingga penangkapan...")
        
        if st.button("Simpan Kronologi", type="primary"):
            st.session_state.data_asesmen['kronologi'] = {
                'kronologi_text': kronologi
            }
            st.success("Kronologi tersimpan!")
    
    # ======================================================================
    # TAB 3: PENGGUNAAN NARKOTIKA
    # ======================================================================
    with tab3:
        st.header("III. PENGGUNAAN NARKOTIKA")
        
        st.subheader("1. Penggunaan Narkotika Saat Ini")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**A. Jenis Narkotika**")
            jenis_narkotika = st.multiselect(
                "Pilih semua jenis narkotika yang digunakan:",
                JENIS_NARKOTIKA,
                key="jenis_narkotika"
            )
            
            if "Lainnya" in jenis_narkotika:
                jenis_lain = st.text_input("Sebutkan jenis narkotika lainnya:", key="jenis_lain")
            else:
                jenis_lain = ""
        
        with col2:
            st.markdown("**B. Hasil Pemeriksaan Urine**")
            hasil_urine = st.radio(
                "Hasil tes urine:",
                ["Positif", "Negatif"],
                key="hasil_urine"
            )
            
            if hasil_urine == "Positif":
                zat_positif = st.multiselect(
                    "Zat yang terdeteksi positif:",
                    JENIS_NARKOTIKA,
                    key="zat_positif"
                )
            else:
                zat_positif = []
        
        st.markdown("---")
        
        st.subheader("2. Riwayat Penggunaan")
        durasi_penggunaan = st.number_input(
            "Berapa lama sudah menggunakan narkotika? (dalam bulan)*",
            min_value=0,
            max_value=480,
            value=12,
            key="durasi_penggunaan"
        )
        
        frekuensi = st.selectbox(
            "Frekuensi penggunaan:",
            ["Harian", "Mingguan", "Bulanan", "Sesekali"],
            key="frekuensi"
        )
        
        cara_pakai = st.selectbox(
            "Cara penggunaan:",
            ["Dihisap", "Disuntik", "Ditelan", "Dihirup", "Lainnya"],
            key="cara_pakai"
        )
        
        if st.button("Simpan Data Narkotika", type="primary"):
            st.session_state.data_asesmen['narkotika'] = {
                'jenis_narkotika': jenis_narkotika,
                'jenis_lain': jenis_lain,
                'hasil_urine': hasil_urine,
                'zat_positif': zat_positif,
                'durasi_penggunaan': durasi_penggunaan,
                'frekuensi': frekuensi,
                'cara_pakai': cara_pakai
            }
            st.success("Data penggunaan narkotika tersimpan!")
    
    # ======================================================================
    # TAB 4: STATUS HUKUM
    # ======================================================================
    with tab4:
        st.header("IV. STATUS HUKUM")
        
        st.subheader("1. Riwayat Tindak Pidana")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Riwayat Kasus:**")
            narkotika = st.checkbox("Narkotika")
            psikotropika = st.checkbox("Psikotropika")
            pencurian = st.checkbox("Pencurian")
            perampokan = st.checkbox("Perampokan")
        
        with col2:
            st.markdown("**Lanjutan:**")
            pembunuhan = st.checkbox("Pembunuhan")
            pemerkosaan = st.checkbox("Pemerkosaan")
            lainnya_hukum = st.checkbox("Lainnya")
            
            if lainnya_hukum:
                lainnya_text = st.text_input("Sebutkan jenis kasus lainnya:")
            else:
                lainnya_text = ""
        
        st.markdown("---")
        
        st.subheader("2. Riwayat Penahanan")
        
        col3, col4 = st.columns(2)
        
        with col3:
            jumlah_penahanan = st.number_input("Berapa kali pernah ditahan?", min_value=0, max_value=20, value=0)
            tempat_penahanan = st.text_input("Tempat penahanan terakhir:")
        
        with col4:
            tanggal_penahanan = st.date_input("Tanggal penahanan terakhir:", value=date.today())
            lama_penahanan = st.number_input("Lama penahanan (hari):", min_value=0, max_value=365, value=0)
        
        status_penahanan = st.selectbox(
            "Status penahanan terakhir:",
            ["Masih ditahan", "Bebas demi hukum", "Penangguhan penahanan", "Proses hukum lanjut"]
        )
        
        st.markdown("---")
        
        st.subheader("3. Riwayat Persidangan")
        
        col5, col6 = st.columns(2)
        
        with col5:
            pernah_sidang = st.checkbox("Pernah menjalani persidangan")
            if pernah_sidang:
                jenis_tindak_pidana = st.text_input("Jenis tindak pidana:")
                vonis = st.text_input("Vonis hakim:")
        
        with col6:
            if pernah_sidang:
                tempat_hukuman = st.text_input("Ditempatkan di Rutan/Lapas:")
        
        st.markdown("---")
        
        st.subheader("4. Keterlibatan dalam Jaringan")
        
        st.markdown("**A. Jenis Narkotika yang Dimiliki Saat Penangkapan**")
        jenis_narkotika_sita = st.multiselect(
            "Pilih jenis narkotika yang disita:",
            ["Heroin", "Ganja", "Ekstasi", "Sabu", "Kokain", "Carisoprodol", "Cannabinoid Sintesis", "Lainnya"]
        )
        
        st.markdown("**B. Tujuan Kepemilikan Narkotika**")
        tujuan_narkotika = st.selectbox(
            "Narkotika yang dimiliki untuk:",
            ["Dipakai sendiri", "Dipakai bersama-sama", "Titipan orang", "Akan dijual", "Lainnya"]
        )
        
        st.markdown("**C. Metode Pembelian Narkotika**")
        metode_beli = st.selectbox(
            "Cara mendapatkan narkotika:",
            ["Beli langsung", "Dari teman", "Dari jaringan tertentu", "Aplikasi/media sosial", "Lainnya"]
        )
        
        metode_bayar = st.selectbox(
            "Metode pembayaran:",
            ["Cash", "Transfer bank", "Uang elektronik", "Tukar barang", "Lainnya"]
        )
        
        st.markdown("**D. Pengecekan Database Intelijen**")
        cek_database = st.text_area("Hasil pengecekan database intelijen:")
        
        st.markdown("**E. Fakta Hukum**")
        fakta_hukum = st.text_area("Fakta-fakta hukum yang terungkap:")
        
        if st.button("Simpan Data Hukum", type="primary"):
            st.session_state.data_asesmen['hukum'] = {
                'riwayat_narkotika': narkotika,
                'riwayat_psikotropika': psikotropika,
                'riwayat_pencurian': pencurian,
                'riwayat_perampokan': perampokan,
                'riwayat_pembunuhan': pembunuhan,
                'riwayat_pemerkosaan': pemerkosaan,
                'riwayat_lainnya': lainnya_text,
                'jumlah_penahanan': jumlah_penahanan,
                'tempat_penahanan': tempat_penahanan,
                'tanggal_penahanan': tanggal_penahanan,
                'lama_penahanan': lama_penahanan,
                'status_penahanan': status_penahanan,
                'pernah_sidang': pernah_sidang,
                'jenis_tindak_pidana': jenis_tindak_pidana if pernah_sidang else "",
                'vonis': vonis if pernah_sidang else "",
                'tempat_hukuman': tempat_hukuman if pernah_sidang else "",
                'jenis_narkotika_sita': jenis_narkotika_sita,
                'tujuan_narkotika': tujuan_narkotika,
                'metode_beli': metode_beli,
                'metode_bayar': metode_bayar,
                'cek_database': cek_database,
                'fakta_hukum': fakta_hukum,
                'jenis_narkotika': jenis_narkotika_sita[0] if jenis_narkotika_sita else "Lainnya",
                'barang_bukti': st.session_state.data_asesmen.get('narkotika', {}).get('barang_bukti', 0),
                'keterlibatan_jaringan': tujuan_narkotika,
                'riwayat_pidana': "First offender (pertama kali)" if jumlah_penahanan == 0 else "Pernah ditahan sebelumnya",
                'status_penangkapan': status_penahanan
            }
            st.success("Data hukum tersimpan!")
    
    # ======================================================================
    # TAB 5: ASESMEN MEDIS
    # ======================================================================
    with tab5:
        st.header("V. ASESMEN MEDIS")
        
        st.subheader("A. Instrumen ASAM (6 Dimensi)")
        
        st.markdown("**1. Kondisi Intoksikasi/Withdrawal Akut**")
        kondisi_akut = st.slider("Skor kondisi akut (0-10):", 0, 10, 3)
        
        st.markdown("**2. Kondisi Biomedis**")
        kondisi_biomedis = st.slider("Skor kondisi biomedis (0-10):", 0, 10, 2)
        
        st.markdown("**3. Kondisi Emosional, Perilaku, dan Kognitif**")
        kondisi_emosional = st.slider("Skor kondisi emosional (0-10):", 0, 10, 4)
        
        st.markdown("**4. Kesiapan Berubah**")
        kesiapan_berubah = st.slider("Skor kesiapan berubah (0-10):", 0, 10, 5)
        
        st.markdown("**5. Potensi Relaps**")
        potensi_relaps = st.slider("Skor potensi relaps (0-10):", 0, 10, 6)
        
        st.markdown("**6. Lingkungan Pemulihan**")
        lingkungan_pemulihan = st.slider("Skor lingkungan pemulihan (0-10):", 0, 10, 3)
        
        st.markdown("---")
        
        st.subheader("B. Diagnosis PPDGJ III")
        diagnosis_ppdgj = st.multiselect(
            "Pilih diagnosis sesuai PPDGJ III:",
            PPDGJ_CRITERIA
        )
        
        st.markdown("---")
        
        st.subheader("C. ICD-10 Diagnosis")
        icd10_diagnosis = st.text_input(
            "Diagnosis ICD-10:",
            value="F15.2 - Gangguan Mental dan Perilaku akibat Penggunaan Stimulan Lain (Amfetamin)"
        )
        
        st.markdown("---")
        
        st.subheader("D. Rekomendasi Medis")
        rekomendasi_medis = st.selectbox(
            "Rekomendasi penanganan medis:",
            [
                "Rehabilitasi Rawat Jalan",
                "Rehabilitasi Rawat Inap (3 bulan)",
                "Rehabilitasi Rawat Inap (6 bulan)",
                "Rehabilitasi Rawat Inap (12 bulan)",
                "Perawatan Intensif di RS Jiwa",
                "Konseling Rutin"
            ]
        )
        
        if st.button("Simpan Data Medis", type="primary"):
            st.session_state.data_asesmen['medis'] = {
                'asam_scores': {
                    'kondisi_akut': kondisi_akut,
                    'kondisi_biomedis': kondisi_biomedis,
                    'kondisi_emosional': kondisi_emosional,
                    'kesiapan_berubah': kesiapan_berubah,
                    'potensi_relaps': potensi_relaps,
                    'lingkungan_pemulihan': lingkungan_pemulihan
                },
                'diagnosis_ppdgj': diagnosis_ppdgj,
                'icd10_diagnosis': icd10_diagnosis,
                'rekomendasi_medis': rekomendasi_medis,
                'total_asam_score': kondisi_akut + kondisi_biomedis + kondisi_emosional + 
                                   kesiapan_berubah + potensi_relaps + lingkungan_pemulihan
            }
            st.success("Data medis tersimpan!")
    
    # ======================================================================
    # TAB 6: HASIL ANALISIS
    # ======================================================================
    with tab6:
        st.header("📊 HASIL ANALISIS TERPADU")
        
        if st.button("🚀 PROSES ANALISIS", type="primary", use_container_width=True):
            with st.spinner("Sedang menganalisis data..."):
                # Analisis medis
                hasil_medis = analisis_medis(
                    st.session_state.data_asesmen['narkotika'],
                    st.session_state.data_asesmen['medis']
                )
                
                # Analisis hukum
                hasil_hukum = analisis_hukum(
                    st.session_state.data_asesmen['hukum'],
                    st.session_state.data_asesmen['narkotika']
                )
                
                # Gabungkan hasil
                st.session_state.hasil_analisis = {
                    'tanggal_asesmen': datetime.now().strftime("%d %B %Y"),
                    'nomor_surat': f"BNN-KALUT/{datetime.now().strftime('%m')}/{datetime.now().strftime('%Y')}/001",
                    'hasil_medis': hasil_medis,
                    'hasil_hukum': hasil_hukum,
                    'diagnosis_medis': hasil_medis['diagnosis'],
                    'kesimpulan': f"Berdasarkan hasil asesmen terpadu, {st.session_state.data_asesmen['demografi']['nama']} teridentifikasi sebagai {hasil_hukum['kategori_hukum'].lower()} dengan tingkat kecanduan {hasil_medis['tingkat_kecanduan'].lower()}.",
                    'rekomendasi': f"{hasil_medis['rekomendasi_medis']}. {hasil_hukum['rekomendasi_hukum']}",
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            st.success("Analisis selesai!")
        
        if st.session_state.hasil_analisis:
            hasil = st.session_state.hasil_analisis
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Diagnosis Medis", hasil['hasil_medis']['diagnosis'])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Tingkat Kecanduan", hasil['hasil_medis']['tingkat_kecanduan'])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Kategori Hukum", hasil['hasil_hukum']['kategori_hukum'])
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.subheader("📋 KESIMPULAN")
            st.markdown(f'<div class="info-box">{hasil["kesimpulan"]}</div>', unsafe_allow_html=True)
            
            st.subheader("🎯 REKOMENDASI")
            if "Rehabilitasi" in hasil['rekomendasi'] and "Proses hukum" not in hasil['rekomendasi']:
                box_class = "success-box"
            elif "Proses hukum" in hasil['rekomendasi']:
                box_class = "warning-box"
            else:
                box_class = "info-box"
            
            st.markdown(f'<div class="{box_class}">{hasil["rekomendasi"]}</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.subheader("📈 DETAIL ANALISIS")
            
            tab_detail1, tab_detail2 = st.tabs(["🏥 Asesmen Medis", "⚖️ Asesmen Hukum"])
            
            with tab_detail1:
                st.markdown("**Skor ASAM:**")
                skor_asam = hasil['hasil_medis']['skor_asam']
                
                fig_asam = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=skor_asam,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Total Skor ASAM", 'font': {'size': 20}},
                    gauge={
                        'axis': {'range': [None, 10]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 3], 'color': "lightgreen"},
                            {'range': [3, 7], 'color': "yellow"},
                            {'range': [7, 10], 'color': "red"}
                        ]
                    }
                ))
                st.plotly_chart(fig_asam, use_container_width=True)
                
                st.markdown("**Rekomendasi Medis:**")
                st.info(hasil['hasil_medis']['rekomendasi_medis'])
            
            with tab_detail2:
                st.markdown("**Indikasi Keterlibatan Jaringan:**")
                st.warning(hasil['hasil_hukum']['indikasi_jaringan'])
                
                st.markdown("**Kesimpulan Hukum:**")
                st.info(hasil['hasil_hukum']['kesimpulan_hukum'])
    
    # ======================================================================
    # TAB 7: GENERATE SURAT
    # ======================================================================
    with tab7:
        st.header("📄 GENERATE SURAT RESMI")
        
        if not st.session_state.data_asesmen['demografi']:
            st.warning("⚠️ Harap lengkapi data demografi terlebih dahulu di Tab 1.")
        elif not st.session_state.hasil_analisis:
            st.warning("⚠️ Harap lakukan analisis terlebih dahulu di Tab 6.")
        else:
            st.success("✅ Data siap untuk generate surat.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📝 Surat dalam format Word")
                if st.button("📄 Generate Surat Word", use_container_width=True):
                    with st.spinner("Membuat dokumen Word..."):
                        word_file = generate_word_document(
                            st.session_state.data_asesmen,
                            st.session_state.hasil_analisis
                        )
                        
                        st.download_button(
                            label="⬇️ Download Surat (.docx)",
                            data=word_file,
                            file_name=f"Surat_Hasil_Asesmen_{st.session_state.data_asesmen['demografi']['nama'].replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            
            with col2:
                st.subheader("📘 Surat dalam format PDF")
                if st.button("📘 Generate Surat PDF", use_container_width=True):
                    with st.spinner("Membuat dokumen PDF..."):
                        pdf_file = generate_pdf_document(
                            st.session_state.data_asesmen,
                            st.session_state.hasil_analisis
                        )
                        
                        st.download_button(
                            label="⬇️ Download Surat (.pdf)",
                            data=pdf_file,
                            file_name=f"Surat_Hasil_Asesmen_{st.session_state.data_asesmen['demografi']['nama'].replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            
            st.markdown("---")
            
            st.subheader("🔍 Preview Data Surat")
            
            col_preview1, col_preview2 = st.columns(2)
            
            with col_preview1:
                st.markdown("**Data Demografi:**")
                demografi = st.session_state.data_asesmen['demografi']
                preview_data = [
                    ("Nama", demografi.get('nama', '-')),
                    ("NIK", demografi.get('nik', '-')),
                    ("TTL", f"{demografi.get('tempat_lahir', '-')}, {demografi.get('tanggal_lahir', '-')}"),
                    ("Jenis Kelamin", demografi.get('jenis_kelamin', '-')),
                    ("Kewarganegaraan", demografi.get('kewarganegaraan', '-'))
                ]
                
                for label, value in preview_data:
                    st.markdown(f"**{label}:** {value}")
            
            with col_preview2:
                st.markdown("**Hasil Analisis:**")
                hasil = st.session_state.hasil_analisis
                preview_hasil = [
                    ("Diagnosis", hasil.get('diagnosis_medis', '-')),
                    ("Kesimpulan", hasil.get('kesimpulan', '-')[:100] + "..."),
                    ("Rekomendasi", hasil.get('rekomendasi', '-')[:100] + "...")
                ]
                
                for label, value in preview_hasil:
                    st.markdown(f"**{label}:** {value}")

# =============================================================================
# JALANKAN APLIKASI
# =============================================================================
if __name__ == "__main__":
    main()
