import streamlit as st
import pandas as pd
import openpyxl
import io

st.set_page_config(page_title="NOON Template Filler", layout="wide")

st.title("NOON Information Sheet Generator")
st.write("Upload your source data and the NOON template. The app will preserve formatting and auto-match headers intelligently.")

# Smart matching helper function
def find_best_match(template_header, source_headers):
    temp_clean = str(template_header).lower().strip()
    
    # 1. Look for an exact match (ignoring upper/lower case)
    for src in source_headers:
        if temp_clean == str(src).lower().strip():
            return src
            
    # 2. Look for keyword matches (e.g., "Color" matches "Product Color")
    for src in source_headers:
        src_clean = str(src).lower().strip()
        if src_clean in temp_clean or temp_clean in src_clean:
            return src
            
    return None

col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("1. Upload Source Data (Excel/CSV)", type=["csv", "xlsx"])
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

        # Load NOON template
        wb = openpyxl.load_workbook(template_file)
        sheet = wb.active 
        
        # Extract headers from Row 8
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
        st.write("Headers mapped automatically based on keywords. Please review before generating.")
        
        mapping = {}
        source_options = ["--- Leave Empty ---"] + source_headers
        
        # Create mapping interface with Smart Matching
        for header in template_headers:
            default_index = 0
            
            # Use our new function to find the best match
            best_match = find_best_match(header, source_headers)
            if best_match:
                default_index = source_options.index(best_match)
                
            selected_col = st.selectbox(
                f"NOON Template Header: **{header}**", 
                options=source_options, 
                index=default_index
            )
            
            if selected_col != "--- Leave Empty ---":
                mapping[header] = selected_col
            else:
                mapping[header] = None

        # Generate the final file
        if st.button("Generate NOON Sheet", type="primary"):
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
