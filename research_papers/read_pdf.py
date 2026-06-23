import sys
try:
    import fitz # PyMuPDF
    doc = fitz.open(sys.argv[1])
    text = ""
    for page in doc:
        text += page.get_text()
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        f.write(text)
    print("Success PyMuPDF")
    sys.exit(0)
except ImportError:
    pass

try:
    import PyPDF2
    with open(sys.argv[1], 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        f.write(text)
    print("Success PyPDF2")
    sys.exit(0)
except ImportError:
    print("NO_PDF_LIB")
    sys.exit(1)
