import zipfile, textwrap, os

# --- content.xml ---
content = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  office:version="1.3">
  <office:automatic-styles/>
  <office:body>
    <office:text>

      <!-- Heading 1: First Section -->
      <text:h text:style-name="Heading 1" text:outline-level="1">Part One: The Beginning</text:h>

      <!-- Body paragraphs -->
      <text:p text:style-name="Text Body">In our first paragraph, we&#x2019;ll begin. From there, we&#x2019;ll proceed through each step to the logical conclusion.</text:p>

      <text:p text:style-name="Text Body">The second paragraph arrives as all second paragraphs do: after the first, before the third, uncertain of its own necessity. It contains <text:span text:style-name="Bold">bold text</text:span> to demonstrate inline formatting, and <text:span text:style-name="Emphasis">italic text</text:span> to prove the point further. Both must survive the round-trip or we will know what was lost.</text:p>

      <text:p text:style-name="Text Body">A third paragraph, for completeness. The body text confirms itself simply by existing.</text:p>

      <!-- Bulleted list -->
      <text:list text:style-name="List Bullet">
        <text:list-item>
          <text:p text:style-name="List Bullet">The first item, which precedes the second</text:p>
        </text:list-item>
        <text:list-item>
          <text:p text:style-name="List Bullet">The second item, which follows the first</text:p>
        </text:list-item>
        <text:list-item>
          <text:p text:style-name="List Bullet">The third item, which neither precedes nor follows anything further</text:p>
        </text:list-item>
      </text:list>

      <!-- Heading 1: Second Section -->
      <text:h text:style-name="Heading 1" text:outline-level="1">Part Two: The Continuation</text:h>

      <!-- H2 under second section -->
      <text:h text:style-name="Heading 2" text:outline-level="2">A Subsection</text:h>

      <text:p text:style-name="Text Body">The second section exists to confirm that sections are not collapsed, dropped, or merged into the first. It has its own heading, which pandoc must recognize by paragraph style rather than by visual resemblance to a heading.</text:p>

      <text:p text:style-name="Text Body">And so we arrive at the final paragraph. It contains both <text:span text:style-name="Bold">bold</text:span> and <text:span text:style-name="Emphasis">italic</text:span> and, in the end, nothing more is required of it.</text:p>

    </office:text>
  </office:body>
</office:document-content>'''

# --- styles.xml — defines the named paragraph/character styles ---
styles = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  office:version="1.3">
  <office:styles>

    <!-- Default paragraph style -->
    <style:default-style style:family="paragraph">
      <style:text-properties fo:font-size="12pt" fo:font-family="Liberation Serif"/>
    </style:default-style>

    <!-- Heading 1 -->
    <style:style style:name="Heading 1" style:display-name="Heading 1"
                 style:family="paragraph" style:parent-style-name="Heading"
                 style:next-style-name="Text Body"
                 text:outline-level="1">
      <style:text-properties fo:font-size="18pt" fo:font-weight="bold"/>
    </style:style>

    <!-- Heading 2 -->
    <style:style style:name="Heading 2" style:display-name="Heading 2"
                 style:family="paragraph" style:parent-style-name="Heading"
                 style:next-style-name="Text Body"
                 text:outline-level="2">
      <style:text-properties fo:font-size="14pt" fo:font-weight="bold" fo:font-style="italic"/>
    </style:style>

    <!-- Text Body -->
    <style:style style:name="Text Body" style:display-name="Text Body"
                 style:family="paragraph">
      <style:paragraph-properties fo:margin-bottom="6pt"/>
      <style:text-properties fo:font-size="12pt"/>
    </style:style>

    <!-- List Bullet -->
    <style:style style:name="List Bullet" style:display-name="List Bullet"
                 style:family="paragraph">
      <style:paragraph-properties fo:margin-left="1.27cm" fo:text-indent="-0.635cm"/>
      <style:text-properties fo:font-size="12pt"/>
    </style:style>

    <!-- Bold character style -->
    <style:style style:name="Bold" style:family="text">
      <style:text-properties fo:font-weight="bold"/>
    </style:style>

    <!-- Emphasis character style -->
    <style:style style:name="Emphasis" style:family="text">
      <style:text-properties fo:font-style="italic"/>
    </style:style>

  </office:styles>
</office:document-styles>'''

# --- mimetype (must be first, uncompressed) ---
mimetype = "application/vnd.oasis.opendocument.text"

# --- manifest ---
manifest = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
                   manifest:version="1.3">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="META-INF/manifest.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''

out = os.path.join(os.path.dirname(__file__), "valid_odt.odt")
os.makedirs(os.path.dirname(out), exist_ok=True)

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    # mimetype must be first and stored (not compressed)
    z.writestr(zipfile.ZipInfo("mimetype"), mimetype)
    z.writestr("content.xml", content)
    z.writestr("styles.xml", styles)
    z.writestr("META-INF/manifest.xml", manifest)

print("Written:", out)
print("Size:", os.path.getsize(out), "bytes")
