# Smart matching helper function customized for Amazon -> NOON mapping
def find_best_match(template_header, source_headers):
    temp_clean = str(template_header).lower().strip()
    
    # 1. Custom Amazon-to-NOON Dictionary Map
    # Key = NOON Header, Value = Amazon Header
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
    
    # Check if the NOON header has known Amazon equivalents in our dictionary
    if temp_clean in custom_mapping:
        possible_amazon_names = custom_mapping[temp_clean]
        for src in source_headers:
            if str(src).lower().strip() in possible_amazon_names:
                return src

    # 2. Look for an exact match (ignoring upper/lower case)
    for src in source_headers:
        if temp_clean == str(src).lower().strip():
            return src
            
    # 3. Look for keyword matches as a fallback (e.g., "Color" matches "Product Color")
    for src in source_headers:
        src_clean = str(src).lower().strip()
        if src_clean in temp_clean or temp_clean in src_clean:
            # Prevent weird mismatches like "Item" matching "Item Condition" when it shouldn't
            if len(src_clean) > 4: 
                return src
            
    return None
