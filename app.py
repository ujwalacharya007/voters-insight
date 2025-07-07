import streamlit as st
import io
import pandas as pd
import re
import platform
from PyPDF2 import PdfReader, PdfWriter
from pypdf import PdfReader as MergeReader, PdfWriter as MergeWriter
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import plotly.graph_objects as go

st.set_page_config(page_title="📊 Unified PDF Insight System", layout="wide")

# Language selector
language = st.selectbox("Choose Language / भाषा छान्नुहोस्", ["English", "नेपाली"], index=0)

# Translations
T = {
    "English": {
        "split": "📄 Split PDF", "merge": "🧩 Merge PDFs", "ocr": "🧠 OCR Extract", "insight": "📊 Excel Insights",
        "upload_pdf_split": "Upload a PDF to split", "start_page": "Start Page", "end_page": "End Page", "download_split": "📥 Download Split PDF",
        "upload_pdf_merge": "Choose PDF files to merge", "download_merged": "📥 Download Merged PDF",
        "upload_pdf_ocr": "📤 Upload scanned PDF for OCR", "download_excel": "📥 Download Excel File",
        "ocr_processing": "🔄 OCR in progress. Please wait...", "ocr_done": "✅ OCR completed. Extracting structured data...",
        "no_data": "⚠️ No structured data matched.",
        "upload_excel": "📤 Upload Excel File", "age_chart": "📈 Show Age Group Pie Chart",
        "gender_chart": "🧭 Show Gender Distribution", "gender_chart_type": "Chart Type",
        "caste_chart": "🏷️ Show Castes by Gender", "upload_warning": "📄 Please upload an Excel file with columns 'उमेर', 'लिङ्ग', 'जाति'."
    },
    "नेपाली": {
        "split": "📄 PDF पेज काट्ने", "merge": "🧩 PDF मिसाउने", "ocr": "🧠 OCR नाम निकाल्ने", "insight": "📊 Excel डाटा विश्लेषण",
        "upload_pdf_split": "PDF अपलोड गर्नुहोस् जसलाई काट्न चाहनुहुन्छ", "start_page": "सुरुको पेज", "end_page": "अन्तिम पेज", "download_split": "📥 काटिएको PDF डाउनलोड गर्नुहोस्",
        "upload_pdf_merge": "मिसाउन PDF फाइलहरू छान्नुहोस्", "download_merged": "📥 मिसाइएको PDF डाउनलोड गर्नुहोस्",
        "upload_pdf_ocr": "📤 OCR गर्न PDF फाइल अपलोड गर्नुहोस्", "download_excel": "📥 Excel फाइल डाउनलोड गर्नुहोस्",
        "ocr_processing": "🔄 OCR हुँदैछ... कृपया प्रतिक्षा गर्नुहोस्...", "ocr_done": "✅ OCR सकियो। डाटा निकालिँदैछ...",
        "no_data": "⚠️ डाटा मिलेन।", "upload_excel": "📤 Excel फाइल अपलोड गर्नुहोस्",
        "age_chart": "📈 उमेर समूह चार्ट देखाउनुहोस्", "gender_chart": "🧭 लिङ्ग वितरण देखाउनुहोस्",
        "gender_chart_type": "चार्ट प्रकार", "caste_chart": "🏷️ जाति अनुसार लिङ्ग चार्ट",
        "upload_warning": "📄 कृपया 'उमेर', 'लिङ्ग', 'जाति' भएका Excel फाइल अपलोड गर्नुहोस्।"
    }
}
labels = T[language]

tabs = st.tabs([labels["split"], labels["merge"], labels["ocr"], labels["insight"]])

# -------------------- Split PDF (Optimized for Large Files) ---------------------
with tabs[0]:
    st.header(labels["split"])
    uploaded_file = st.file_uploader(labels["upload_pdf_split"], type=["pdf"], key="split_pdf")
    start_page = st.number_input(labels["start_page"], min_value=1, step=1)
    end_page = st.number_input(labels["end_page"], min_value=1, step=1)

    if uploaded_file and start_page <= end_page:
        try:
            uploaded_bytes = uploaded_file.read()  # read as bytes to avoid stream exhaustion
            reader = PdfReader(io.BytesIO(uploaded_bytes))
            total_pages = len(reader.pages)
            start_idx = start_page - 1
            end_idx = min(end_page, total_pages)

            if start_idx >= total_pages:
                st.error("🚫 Start page exceeds total page count.")
            else:
                writer = PdfWriter()
                for i in range(start_idx, end_idx):
                    writer.add_page(reader.pages[i])

                output = io.BytesIO()
                writer.write(output)
                output.seek(0)

                st.success("✅ PDF split successfully!")
                st.download_button(
                    label=labels["download_split"],
                    data=output,
                    file_name="split_output.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"❌ Error splitting PDF: {str(e)}")


# -------------------- Merge PDF ---------------------
with tabs[1]:
    st.header(labels["merge"])
    uploaded_files = st.file_uploader(labels["upload_pdf_merge"], type="pdf", accept_multiple_files=True, key="merge_pdf")

    if uploaded_files:
        writer = MergeWriter()
        try:
            for file in uploaded_files:
                reader = MergeReader(file)
                for page in reader.pages:
                    writer.add_page(page)

            merged_pdf = io.BytesIO()
            writer.write(merged_pdf)
            merged_pdf.seek(0)

            st.success("✅ PDFs merged successfully!")
            st.download_button(labels["download_merged"], data=merged_pdf, file_name="merged_output.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# -------------------- OCR Extract to Excel ---------------------

import platform

if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Admin\Tesseract-OCR\Tesseract-OCR\tesseract.exe'
else:
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
with tabs[2]:
    st.header(labels["ocr"])
    uploaded_file = st.file_uploader(labels["upload_pdf_ocr"], type="pdf", key="ocr_pdf")

    if uploaded_file:
        try:
            st.info(labels["ocr_processing"])
            images = convert_from_bytes(uploaded_file.read(), dpi=383)
            num_pages = len(images)
            progress_bar = st.progress(0)
            all_text = ""

            for i, image in enumerate(images):
                progress_bar.progress((i + 1) / num_pages)
                gray_image = image.convert("L")
                binary_image = gray_image.point(lambda x: 0 if x < 200 else 255, '1')
                text = pytesseract.image_to_string(binary_image, lang='nep')
                all_text += f"Page {i + 1}:\n{text}\n\n"
                st.text_area(f"📝 OCR Preview (Page {i+1})", value=text[:500], height=100, key=f"preview_{i}", disabled=True)

            st.success(labels["ocr_done"])

            pattern = re.compile(r'([^\d\.\n]+?)\s+(\d+)\s+वर्ष\s+/\s+(पुरुष|महिला)\s+([^\n]+)')
            matches = re.findall(pattern, all_text)

            if not matches:
                st.warning(labels["no_data"])
            else:
                data = {
                    'नाम': [match[0].strip() for match in matches],
                    'उमेर': [int(match[1]) for match in matches],
                    'लिङ्ग': [match[2] for match in matches],
                    'जाति': [match[0].strip().split()[-1] for match in matches]
                }
                df = pd.DataFrame(data)
                st.dataframe(df.head(50), use_container_width=True)

                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Extracted Data')
                excel_buffer.seek(0)

                st.download_button(labels["download_excel"], data=excel_buffer, file_name="extracted_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# -------------------- Excel Visualization ---------------------
# -------------------- Excel Visualization ---------------------
with tabs[3]:
    st.header("📊 Excel डाटा विश्लेषण")
    excel_file = st.file_uploader("📤 Excel फाइल अपलोड गर्नुहोस्", type=["xlsx"], key="excel_file")

    def convert_to_nepali_number(num):
        eng = '0123456789'
        nep = '०१२३४५६७८९'
        return ''.join(nep[eng.index(ch)] if ch in eng else ch for ch in str(num))

    if excel_file:
        df = pd.read_excel(excel_file)
        df['जाति'] = df['जाति'].astype(str).str.strip().replace({
            'गुरुङ्ग': 'गुरुङ', 'गुरूङ्ग': 'गुरुङ', 'गुरूङ': 'गुरुङ'
        })

        def categorize_age(age):
            if age < 20:
                return '<20'
            elif age <= 35:
                return '21–35'
            elif age <= 50:
                return '36–50'
            else:
                return '51+'

        df['उमेर समूह'] = df['उमेर'].apply(categorize_age)
        age_labels = {'<20': '२० वर्ष मुनि', '21–35': '२१ देखि ३५ वर्ष', '36–50': '३६ देखि ५० वर्ष', '51+': '५१ वर्ष माथि'}
        order = ['<20', '21–35', '36–50', '51+']
        age_counts = df['उमेर समूह'].value_counts().reindex(order, fill_value=0)

        # Summary KPIs
        कुल_व्यक्ति = len(df)
        औसत_उमेर = round(df['उमेर'].mean(), 1)
        पुरुष_संख्या = (df['लिङ्ग'] == 'पुरुष').sum()
        महिला_संख्या = (df['लिङ्ग'] == 'महिला').sum()
        अन्य_संख्या = कुल_व्यक्ति - (पुरुष_संख्या + महिला_संख्या)

        st.subheader("📋 जनसंख्या विश्लेषण ड्यासबोर्ड")
        st.markdown("""
        यो ड्यासबोर्डले Excel बाट प्राप्त जनसंख्या विवरणलाई नेपाली भाषामा सजिलो तरिकाले प्रस्तुत गर्छ। यहाँ तपाईले:
        - जम्मा व्यक्ति संख्या
        - औसत उमेर
        - लिङ्ग अनुसार वितरण
        - उमेर समूह अनुसार लिङ्ग वितरण
        - जाति अनुसार लिङ्ग अनुपात
        - जाति अनुसार औसत उमेर
        - जाति अनुसार उमेर वितरणको रेखाचित्र
        हेर्न सक्नुहुन्छ।
        """)

        with st.container():
            st.markdown("""
            <style>
            .metric-container {
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                padding: 20px 0;
                background-color: #f4f6f8;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .metric-box {
                text-align: center;
                padding: 10px;
                flex: 1 1 180px;
                border-right: 1px solid #ddd;
            }
            .metric-box:last-child {
                border-right: none;
            }
            .metric-title {
                font-weight: bold;
                font-size: 18px;
                color: #444;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 28px;
                font-weight: bold;
                color: #111;
            }
            </style>
            <div class="metric-container">
                <div class="metric-box">
                    <div class="metric-title">🧍 जम्मा व्यक्ति</div>
                    <div class="metric-value">""" + convert_to_nepali_number(कुल_व्यक्ति) + """</div>
                </div>
                <div class="metric-box">
                    <div class="metric-title">📊 औसत उमेर</div>
                    <div class="metric-value">""" + convert_to_nepali_number(औसत_उमेर) + """</div>
                </div>
                <div class="metric-box">
                    <div class="metric-title">👨‍🦱 पुरुष</div>
                    <div class="metric-value">""" + convert_to_nepali_number(पुरुष_संख्या) + """</div>
                </div>
                <div class="metric-box">
                    <div class="metric-title">👩‍🦱 महिला</div>
                    <div class="metric-value">""" + convert_to_nepali_number(महिला_संख्या) + """</div>
                </div>
                <div class="metric-box">
                    <div class="metric-title">🧑 अन्य</div>
                    <div class="metric-value">""" + convert_to_nepali_number(अन्य_संख्या) + """</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Visualization Placeholders
        st.markdown("### 🔍 थप विवरण हेर्नका लागि तलका विकल्पहरू चयन गर्नुहोस्:")

        if st.checkbox("📈 उमेर समूह अनुसार वितरण"):
            labels_nep = [age_labels[label] for label in order]
            hover = [f"{age_labels[label]}<br>({convert_to_nepali_number(count)} जनसंख्या)" for label, count in zip(order, age_counts)]
            fig = go.Figure(data=[go.Pie(labels=labels_nep, values=age_counts.values, hovertext=hover, hoverinfo="text", textinfo='percent+label')])
            fig.update_layout(title="उमेर समूह अनुसार वितरण")
            st.plotly_chart(fig, use_container_width=True)

        if st.checkbox("🧑‍🤝‍🧑 लिङ्ग अनुसार वितरण"):
            gender_chart = st.radio("चार्ट प्रकार", ["Pie Chart", "Bar Chart"], horizontal=True)
            gender_counts = df['लिङ्ग'].value_counts()
            labels_g = gender_counts.index.tolist()
            values = gender_counts.values.tolist()
            if gender_chart == "Pie Chart":
                fig = go.Figure(data=[go.Pie(labels=labels_g, values=values)])
            else:
                fig = go.Figure(data=[go.Bar(x=labels_g, y=values)])
            fig.update_layout(title="लिङ्ग अनुसार वितरण")
            st.plotly_chart(fig, use_container_width=True)

        if st.checkbox("🏷️ जाति अनुसार लिङ्ग वितरण"):
            top_n = st.slider("शीर्ष जातिहरूको संख्या छान्नुहोस्:", 5, 50, 10)
            top_castes = df['जाति'].value_counts().head(top_n).index.tolist()
            grouped = df[df['जाति'].isin(top_castes)].groupby(['जाति', 'लिङ्ग']).size().unstack(fill_value=0)
            fig = go.Figure()
            for gender in grouped.columns:
                fig.add_bar(x=grouped.index, y=grouped[gender], name=gender)
            fig.update_layout(barmode='stack', title='जाति अनुसार लिङ्ग वितरण')
            st.plotly_chart(fig, use_container_width=True)

        if st.checkbox("📊 उमेर समूह अनुसार लिङ्ग वितरण"):
            gender_age_group = df.groupby(['उमेर समूह', 'लिङ्ग']).size().unstack(fill_value=0)
            fig = go.Figure()
            for gender in gender_age_group.columns:
                fig.add_trace(go.Bar(x=gender_age_group.index, y=gender_age_group[gender], name=gender))
            fig.update_layout(barmode='group', title='उमेर समूह अनुसार लिङ्ग वितरण')
            st.plotly_chart(fig, use_container_width=True)

        if st.checkbox("📏 जाति अनुसार औसत उमेर"):
            top_castes = df['जाति'].value_counts().head(10).index
            avg_age = df[df['जाति'].isin(top_castes)].groupby('जाति')['उमेर'].mean().sort_values()
            fig = go.Figure([go.Bar(x=avg_age.index, y=avg_age.values)])
            fig.update_layout(title="जाति अनुसार औसत उमेर", yaxis_title="औसत उमेर")
            st.plotly_chart(fig, use_container_width=True)

        if st.checkbox("⚖️ जाति अनुसार लिङ्ग प्रतिशत"):
            top_castes = df['जाति'].value_counts().head(10).index
            grouped = df[df['जाति'].isin(top_castes)].groupby(['जाति', 'लिङ्ग']).size().unstack(fill_value=0)
            grouped['Total'] = grouped.sum(axis=1)
            grouped['% महिला'] = (grouped['महिला'] / grouped['Total']) * 100
            grouped['% पुरुष'] = (grouped['पुरुष'] / grouped['Total']) * 100
            fig = go.Figure()
            fig.add_trace(go.Bar(x=grouped.index, y=grouped['% महिला'], name='% महिला'))
            fig.add_trace(go.Bar(x=grouped.index, y=grouped['% पुरुष'], name='% पुरुष'))
            fig.update_layout(barmode='stack', title="जाति अनुसार लिङ्ग प्रतिशत")
            st.plotly_chart(fig, use_container_width=True)

        if st.checkbox("📈 जाति अनुसार उमेर वितरण"):
            age_line = df.groupby(['उमेर', 'जाति']).size().reset_index(name='count')
            fig = go.Figure()
            for caste in age_line['जाति'].unique():
                sub_data = age_line[age_line['जाति'] == caste]
                fig.add_trace(go.Scatter(x=sub_data['उमेर'], y=sub_data['count'], mode='lines+markers', name=caste))
            fig.update_layout(title='जाति अनुसार उमेर वितरण', xaxis_title='उमेर', yaxis_title='संख्या')
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("कृपया 'उमेर', 'लिङ्ग', 'जाति' भएका Excel फाइल अपलोड गर्नुहोस्।")
