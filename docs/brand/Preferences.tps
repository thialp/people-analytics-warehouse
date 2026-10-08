<?xml version='1.0'?>
<!--
  Arcadia Systems color palettes for Tableau.
  Mac:     ~/Documents/My Tableau Public Repository/Preferences.tps
  Windows: Documents\My Tableau Public Repository\Preferences.tps
  If a Preferences.tps already exists there, copy only the <color-palette> blocks into it.
  Restart Tableau Public; the palettes appear under Edit Colors.
-->
<workbook>
  <preferences>
    <!-- Categorical. Keep this order: it was checked for color-blind separation in this order.
         Teal = growth / hires, Coral = leavers / decreases, Violet = internal moves, Amber = highlight only (label it). -->
    <color-palette name="Arcadia Categorical" type="regular">
      <color>#00938D</color>
      <color>#E4572E</color>
      <color>#5B4FB3</color>
      <color>#D98E04</color>
    </color-palette>

    <!-- Sequential: magnitude on one hue (growth %, headcount on a map). -->
    <color-palette name="Arcadia Teal Sequential" type="ordered-sequential">
      <color>#CDEDEA</color>
      <color>#9ED8D2</color>
      <color>#5FBFB7</color>
      <color>#2BA69E</color>
      <color>#00938D</color>
      <color>#007A75</color>
      <color>#00524F</color>
    </color-palette>

    <!-- Diverging: decline (coral) to growth (teal), neutral gray at zero. -->
    <color-palette name="Arcadia Coral-Teal Diverging" type="ordered-diverging">
      <color>#B8401F</color>
      <color>#E4572E</color>
      <color>#F2A68C</color>
      <color>#EFEEEA</color>
      <color>#8ACFC9</color>
      <color>#00938D</color>
      <color>#00615D</color>
    </color-palette>

    <!-- Totals and levels in waterfalls (Opening, Closing), and muted context. -->
    <color-palette name="Arcadia Neutrals" type="regular">
      <color>#13233A</color>
      <color>#5A6170</color>
      <color>#8C8A84</color>
      <color>#C9C7C0</color>
      <color>#ECEBE6</color>
    </color-palette>
  </preferences>
</workbook>
