import streamlit as st
import pandas as pd
import openpyxl
import io
import difflib
import re

st.set_page_config(page_title="NOON Template Filler", layout="wide")

st.title("NOON Information Sheet Generator")
st.write("Upload your Amazon source data and the NOON template. This version includes Fuzzy Matching and Auto-Bullet Splitting.")

def find_best_match(template_header, source_headers):
    temp_clean = str(template_header).lower().strip()
    
    # Custom Dictionary
    custom_mapping = {
        "partner sku unique": ["asin", "item model number", "item_sku", "sku"],
        "brand": ["brand"],
        "product title en": ["title", "item_name", "product name"],
        "long description en": ["product description", "description"],
        "image url 1": ["image 1", "main_image_url"],
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
    
    # 1. Dictionary Match
    if temp_clean in custom_mapping:
        possible_names = custom_mapping[temp_clean]
        for src in source_headers:
            if str(src).lower().strip() in possible_names:
                return src

    source_headers_lower = [str(s).lower().strip() for s in source_headers]

    # 2. Fuzzy Matching (Finds closest match with at least 80% similarity)
    close_matches = difflib.get_close_matches(temp_clean, source_headers_lower, n=1, cutoff=0.8)
    if close_matches:
        match_index = source_headers_lower.index(close_matches[0])
        return source_headers[match_index]
            
    # 3. Keyword Match (Fallback)
    for src in source_headers:
        src_clean = str(src).lower().strip()
        if (src_clean in temp_clean or temp_clean in src_clean) and len(src_clean) > 4:
            return src
            
    return None

col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("1. Upload Amazon Data (Excel/CSV)", type=["csv", "xlsx"])
with col2:
    template_file = st.file_uploader("2. Upload NOON Template (Excel ONLY)", type=["xlsx"])

if source_file and template_file:
    try:
        if source_file.name.endswith('.csv'):
            df_source = pd.read_csv(source_file)
        else:
            df_source = pd.read_excel(source_file)
            
        source_headers = list(df_source.columns)

        wb = openpyxl.load_workbook(template_file)
        sheet = wb.active 
        
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
        
        mapping = {}
        source_options = ["--- Leave Empty ---"] + source_headers
        
        for header in template_headers:
            default_index = 0
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

        if st.button("Generate NOON Sheet", type="primary"):
            start_row = 10
            
            for index, row_data in df_source.iterrows():
                current_row = start_row + index
                
                # --- SMART BULLET SPLITTING LOGIC ---
                # Check if Amazon's 'About This Item' is present in this row
                amazon_bullets = ""
                if "About This Item" in source_headers:
                    val = row_data["About This Item"]
                    if not pd.isna(val):
                        amazon_bullets = str(val)
                
                # Split the text by semicolons or line breaks
                bullet_list = re.split(r';|\n', amazon_bullets)
                bullet_list = [b.strip() for b in bullet_list if b.strip()] # Clean empty strings
                
                for temp_header, source_col in mapping.items():
                    col_idx = header_col_map[temp_header]
                    val = ""
                    
                    if source_col: 
                        val = row_data[source_col]
                        if pd.isna(val):
                            val = ""
                    
                    # Intercept bullet points and apply our split list
                    if "Feature Bullet" in temp_header and "EN" in temp_header:
                        # Extract the bullet number from the header (e.g., "Feature Bullet 1 EN" -> 1)
                        bullet_num_match = re.search(r'\d+', temp_header)
                        if bullet_num_match:
                            bullet_num = int(bullet_num_match.group())
                            # If we have enough split bullets, assign it to the right column
                            if 0 < bullet_num <= len(bullet_list):
                                val = bullet_list[bullet_num - 1]
                            else:
                                val = "" # Leave blank if we run out of bullets
                                
                    sheet.cell(row=current_row, column=col_idx, value=val)
            
            st.success("Data injected successfully with smart bullet formatting!")
            
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
