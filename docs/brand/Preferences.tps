<?xml version='1.0'?>
<!--
  Arcadia Systems color palettes for Tableau: the one source for every Arcadia color.
  Pick colors from these palettes, never with the eyedropper or a typed shade: that is how the
  published workbooks drifted to nine different navies (#13223A, #13243A, #122137, ...).

  Install (replace the whole file; keep a copy of the old one if you have one):
    Tableau Desktop: ~/Documents/My Tableau Repository/Preferences.tps
    Tableau Public:  ~/Documents/My Tableau Public Repository/Preferences.tps
  Restart Tableau. The palettes appear under Edit Colors, numbered so they list together and in order.

  Every categorical order was checked for color-blind separation (protan, deutan, tritan) in this
  order, on the card color #FBFBF8: keep the order. docs/brand/README.md says what each one is for;
  docs/brand/arcadia_palettes.png shows them.
-->
<workbook>
  <preferences>
    <!-- 1. Roles. Teal = growth / hires, Coral = leavers / decreases, Violet = internal moves,
            Amber = one highlight (label it: under 3:1 on the page). -->
    <color-palette name="Arcadia 1 Categorical" type="regular">
      <color>#00938D</color>
      <color>#E4572E</color>
      <color>#5B4FB3</color>
      <color>#D98E04</color>
    </color-palette>

    <!-- 2. Identity for up to nine groups (the four roles first, then blue, green, rose, sky,
            brown). More than nine: fold into "Other". -->
    <color-palette name="Arcadia 2 Categorical Extended" type="regular">
      <color>#00938D</color>
      <color>#E4572E</color>
      <color>#5B4FB3</color>
      <color>#D98E04</color>
      <color>#2F78C4</color>
      <color>#4E9A2E</color>
      <color>#D5679A</color>
      <color>#4FB0E0</color>
      <color>#A8692A</color>
    </color-palette>

    <!-- 3. The same nine as light fills, for large labelled areas with navy text on them
            (Sankey nodes, treemaps): navy text is at least 4.7:1 on every one. Always label. -->
    <color-palette name="Arcadia 3 Categorical Light" type="regular">
      <color>#4CB3AF</color>
      <color>#EC896D</color>
      <color>#8C84CA</color>
      <color>#E4B04F</color>
      <color>#6DA0D6</color>
      <color>#83B86D</color>
      <color>#E295B8</color>
      <color>#84C8E9</color>
      <color>#C2966A</color>
    </color-palette>

    <!-- 4. The systems, wherever they appear: Bridgeway (vendor system), Keystone (HR system),
            the system feed between them. Color follows the system on every dashboard. -->
    <color-palette name="Arcadia 4 Systems" type="regular">
      <color>#D98E04</color>
      <color>#5B4FB3</color>
      <color>#00938D</color>
    </color-palette>

    <!-- 5. Status: on track, watch, at risk, no status. Always with a word ("Low risk"). -->
    <color-palette name="Arcadia 5 Status" type="regular">
      <color>#00938D</color>
      <color>#D98E04</color>
      <color>#E4572E</color>
      <color>#8C8A84</color>
    </color-palette>

    <!-- 6. Neutrals, dark to light: navy (brand ink, rail), navy 2 (controls on the rail),
            slate (borders on navy, secondary bars), text gray, steel, silver (dividers on navy),
            mist, warm gray (totals), hairline, page, card, white. -->
    <color-palette name="Arcadia 6 Neutrals" type="regular">
      <color>#13233A</color>
      <color>#243A57</color>
      <color>#4A5B73</color>
      <color>#5A6170</color>
      <color>#8FA1B8</color>
      <color>#B8C0CD</color>
      <color>#D5DBE4</color>
      <color>#8C8A84</color>
      <color>#E4E3DD</color>
      <color>#F3F3EF</color>
      <color>#FBFBF8</color>
      <color>#FFFFFF</color>
    </color-palette>

    <!-- 7. Sequential: magnitude on one hue (growth %, headcount on a map). -->
    <color-palette name="Arcadia 7 Teal Sequential" type="ordered-sequential">
      <color>#CDEDEA</color>
      <color>#9ED8D2</color>
      <color>#5FBFB7</color>
      <color>#2BA69E</color>
      <color>#00938D</color>
      <color>#007A75</color>
      <color>#00524F</color>
    </color-palette>

    <!-- 8. Sequential on navy: counts and volumes that should stay quiet (vacancy age bars). -->
    <color-palette name="Arcadia 8 Navy Sequential" type="ordered-sequential">
      <color>#E6EAF0</color>
      <color>#D5DBE4</color>
      <color>#B8C4D6</color>
      <color>#8FA1B8</color>
      <color>#4A5B73</color>
      <color>#243A57</color>
      <color>#13233A</color>
    </color-palette>

    <!-- 9. Diverging: decline (coral) to growth (teal), neutral gray at zero. -->
    <color-palette name="Arcadia 9 Coral-Teal Diverging" type="ordered-diverging">
      <color>#B8401F</color>
      <color>#E4572E</color>
      <color>#F2A68C</color>
      <color>#EFEEEA</color>
      <color>#8ACFC9</color>
      <color>#00938D</color>
      <color>#00615D</color>
    </color-palette>
  </preferences>
</workbook>
