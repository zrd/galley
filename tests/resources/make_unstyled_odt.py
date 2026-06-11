import zipfile, os

# An ODT with no recognized paragraph or character styles.
# Pandoc will see the text but won't map it to headings or body content,
# producing near-empty EPUB output — reproducing the BUG-001 symptom.

content = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  office:version="1.3">
  <office:automatic-styles>
    <style:style style:name="BigBold" style:family="paragraph">
      <style:text-properties fo:font-size="18pt" fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="Normal" style:family="paragraph">
      <style:text-properties fo:font-size="12pt"/>
    </style:style>
  </office:automatic-styles>
  <office:body>
    <office:text>
      <text:p text:style-name="BigBold">Part One: The Beginning</text:p>
      <text:p text:style-name="Normal">In our first paragraph, we&#x2019;ll begin.</text:p>
      <text:p text:style-name="Normal">The second paragraph contains visually bold and italic text, but uses no semantic character styles that pandoc recognizes.</text:p>
      <text:p text:style-name="Normal">A third paragraph, for completeness.</text:p>
      <text:p text:style-name="BigBold">Part Two: The Continuation</text:p>
      <text:p text:style-name="Normal">The second section exists to confirm that pandoc does not recover structure from visual formatting alone.</text:p>
    </office:text>
  </office:body>
</office:document-content>'''

styles = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  office:version="1.3">
  <office:styles>
    <style:default-style style:family="paragraph">
      <style:text-properties fo:font-size="12pt" fo:font-family="Liberation Serif"/>
    </style:default-style>
  </office:styles>
</office:document-styles>'''

mimetype = "application/vnd.oasis.opendocument.text"

manifest = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
                   manifest:version="1.3">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="META-INF/manifest.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''

out = os.path.join(os.path.dirname(__file__), "unstyled_odt.odt")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(zipfile.ZipInfo("mimetype"), mimetype)
    z.writestr("content.xml", content)
    z.writestr("styles.xml", styles)
    z.writestr("META-INF/manifest.xml", manifest)

print("Written:", out)
print("Size:", os.path.getsize(out), "bytes")
