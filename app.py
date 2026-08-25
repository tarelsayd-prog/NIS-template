import streamlit as st
import pandas as pd
import openpyxl
import io

st.set_page_config(page_title="NOON Template Filler", layout="wide")

st.title("NOON Information Sheet Generator")
st.write("Upload your Amazon source data and the NOON template. The app will preserve formatting and auto-match headers intelligently.")

# Smart matching helper function customized for Amazon -> NOON mapping
def find_best_match(template_header, source_headers):
    temp_clean = str(template_header).lower().strip()
    
    # Custom Amazon-to-NOON Dictionary Map
    custom_mapping = {
        "partner sku unique": ["asin", "item model number", "item_sku", "sku"],
        "brand": ["brand"],
        "product title en": ["title", "item_name", "product name"],
        "long description en": ["product description", "description"],
        "image url 1": ["image 1", "main_image_url", "main image"],
        "image url 2": ["image 2", "other_image_url1"],
        "image url 3": ["image 3", "other_image_url2"],
        "image url 4": ["image 4", "other_image_url3"],
        "image url 5": ["image 5", "other_image_url4"],
        "image url 6": ["image 6", "other_image_url5"],
        "image url 7": ["image 7", "other_image_url6"],
        "feature bullet 1 en": ["about this item", "bullet point 1", "features"],
        "color": ["color", "colour", "item color"],
        "model": ["model", "item model number"]
    }
    
    # 1. Check dictionary first
    if temp_clean in custom_mapping:
        possible_amazon_names = custom_mapping[temp_clean]
        for src in source_headers:
            if str(src).lower().strip() in possible_amazon_names:
                return src

    # 2. Exact match check
    for src in source_headers:
        if temp_clean == str(src).lower().strip():
            return src
            
    # 3. Partial keyword match check
    for src in source_headers:
        src_clean = str(src).lower().strip()
        if (src_clean in temp_clean or temp_clean in src_clean) and len(src_clean) > 4:
            return src
            
    return None

# File uploaders
col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("1. Upload Amazon Data (Excel/CSV)", type=["csv", "xlsx"])
with col2:
    template_file = st.file_uploader("2. Upload NOON Template (Excel ONLY)", type=["xlsx"])

if source_file and template_file:
    try:
        # Load source data
        if source_file.name.endswith('.csv'):
            df_source = pd.read_csv(source_file)
        else:
            df_source = pd.read_excel(source_file)
            
        source_headers = list(df_source.columns)

        # Load NOON template preserving formatting
        wb = openpyxl.load_workbook(template_file)
        sheet = wb.active 
        
        # Extract headers exactly from Row 8
        template_headers = []
        header_col_map = {} 
        
        for cell in sheet[8]: 
            if cell.value:
                header_name = str(cell.value).strip()
                template_headers.append(header_name)
                header_col_map[header_name] = cell.column

        if not template_headers:
            st.error("Could not find any headers in Row 8 of the template.")
            st.stop()

        st.divider()
        st.subheader("Column Mapping")
        st.write("Headers mapped automatically based on Amazon structure. Please review before generating.")
        
        mapping = {}
        source_options = ["--- Leave Empty ---"] + source_headers
        
        # Create mapping interface with Smart Matching
        for header in template_headers:
            default_index = 0
            
            # Find the best match
            best_match = find_best_match(header, source_headers)
            if best_match:
                default_index = source_options.index(best_match)
                
            selected_col = st.selectbox(
                f"NOON Header: **{header}**", 
                options=source_options, 
                index=default_index
            )
            
            if selected_col != "--- Leave Empty ---":
                mapping[header] = selected_col
            else:
                mapping[header] = None

        # Generate the final file
        if st.button("Generate NOON Sheet", type="primary"):
            # Start writing data at row 10 to preserve hidden row 9
            start_row = 10
            
            for index, row_data in df_source.iterrows():
                current_row = start_row + index
                
                for temp_header, source_col in mapping.items():
                    if source_col: 
                        col_idx = header_col_map[temp_header]
                        val = row_data[source_col]
                        
                        if pd.isna(val):
                            val = ""
                            
                        sheet.cell(row=current_row, column=col_idx, value=val)
            
            st.success("Data injected successfully!")
            
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            st.download_button(
                label="📥 Download Filled NOON Sheet",
                data=buffer.getvalue(),
                file_name="Filled_NOON_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"An error occurred: {e}")
