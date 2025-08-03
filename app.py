from flask import Flask, render_template, request, send_file, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import PyPDF2
from docx import Document
from io import BytesIO
import base64
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def read_txt(file):
    return file.read().decode('utf-8')

def read_docx(file):
    doc = Document(file)
    return ' '.join([para.text for para in doc.paragraphs])

def read_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return ' '.join([page.extract_text() for page in pdf.pages if page.extract_text()])

def generate_wordcloud(text, stopwords, width, height):
    wc = WordCloud(width=width, height=height, background_color='white', stopwords=stopwords, max_words=200)
    return wc.generate(text)

@app.route("/", methods=["GET", "POST"])
def index():
    wordcloud_img = None
    word_count_df = None
    download_link = None

    if request.method == "POST":
        file = request.files.get("file")
        width = int(request.form.get("width", 1200))
        height = int(request.form.get("height", 800))
        use_stopwords = request.form.get("use_stopwords") == "on"
        additional_stopwords = request.form.get("additional_stopwords", "").split(",")
        format_ = request.form.get("format", "png")
        resolution = int(request.form.get("resolution", 300))

        if file:
            ext = file.filename.split('.')[-1].lower()
            if ext == "txt":
                text = read_txt(file)
            elif ext == "pdf":
                text = read_pdf(file)
            elif ext == "docx":
                text = read_docx(file)
            else:
                return "Unsupported file format", 400

            words = text.split()
            word_count_df = pd.DataFrame({'Word': words}).groupby('Word').size().reset_index(name='Count').sort_values(by='Count', ascending=False)

            all_stopwords = STOPWORDS.union(set(additional_stopwords)) if use_stopwords else set(additional_stopwords)

            wc = generate_wordcloud(text, all_stopwords, width, height)
            fig, ax = plt.subplots(figsize=(width / 100, height / 100))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")

            buffer = BytesIO()
            plt.savefig(buffer, format=format_, dpi=resolution)
            buffer.seek(0)

            encoded = base64.b64encode(buffer.read()).decode()
            download_link = f"data:image/{format_};base64,{encoded}"
            buffer.seek(0)
            wordcloud_img = download_link

    return render_template("index.html", wordcloud_img=wordcloud_img, word_count=word_count_df, download_link=download_link)


if __name__ == "__main__":
    import threading
    if threading.current_thread() == threading.main_thread():
        app.run(debug=True)
    else:
        app.run(debug=False)


