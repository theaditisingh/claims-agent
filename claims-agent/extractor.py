import os


def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    if ext == ".pdf":
        return read_pdf(filepath)

    raise ValueError(f"Only .pdf and .txt files are supported. Got: {ext}")


def read_pdf(filepath):
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        result = "\n".join(pages).strip()
        if result:
            return result
    except ImportError:
        pass
    except Exception as e:
        print(f"pdfplumber error: {e}")

    try:
        import PyPDF2
        pages = []
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()
    except ImportError:
        raise ImportError("Install a PDF library: pip install pdfplumber")
    except Exception as e:
        raise RuntimeError(f"Could not read PDF: {e}")