import xml.etree.ElementTree as ET
# Function that converts any data-frame to XML file
def dataframe_to_xml(df, filename):
    root = ET.Element('data')
    for index, row in df.iterrows():
        item = ET.SubElement(root, 'item')
        # for col_name, col_value in row.iteritems():
        for col_name, col_value in row.items():
            # col_value_escaped = escape_special_chars(str(col_value))
            # ET.SubElement(item, col_name).text = col_value_escaped
            ET.SubElement(item, col_name).text = str(col_value)

    tree = ET.ElementTree(root)
    ET.indent(tree, '   ')
    tree.write(filename, encoding='utf-8', xml_declaration=True)
